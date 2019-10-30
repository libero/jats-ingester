"""
DAG processes a zip file stored in an AWS S3 bucket and prepares the extracted xml
file for Libero content API and sends to the content store via a PUT request.
"""
import logging
import re
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import timedelta
from io import BytesIO
from tempfile import TemporaryFile
from typing import List

from airflow import DAG, configuration
from airflow.operators import python_operator
from airflow.utils import timezone

from wand.image import Image

from libero.aws import get_s3_client, list_bucket_keys_iter
from libero.context_facades import (
    get_file_name_passed_to_dag_run_conf_file,
    get_previous_task_name,
    get_return_value_from_previous_task
)
from libero.operators import create_node_task


# settings
ARTICLE_ASSETS_URL = configuration.conf.get('libero', 'article_assets_url')
SOURCE_BUCKET = configuration.conf.get('libero', 'source_bucket_name')
DESTINATION_BUCKET = configuration.conf.get('libero', 'destination_bucket_name')
COMPLETED_TASKS_BUCKET = configuration.conf.get('libero', 'completed_tasks_bucket_name')
SERVICE_NAME = configuration.conf.get('libero', 'service_name')
SERVICE_URL = configuration.conf.get('libero', 'service_url')
TEMP_DIRECTORY = configuration.conf.get('libero', 'temp_directory_path') or None
SEARCH_URL = configuration.conf.get('libero', 'search_url')
WORKERS = configuration.conf.get('libero', 'thread_pool_workers') or None

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'libero',
    'depends_on_past': False,
    'start_date': timezone.utcnow(),
    'email': ['libero@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(seconds=5)
}


def convert_image_in_s3_to_jpeg(key) -> str:
    """
    Downloads a tiff file, converts it to jpeg and uploads it to a predefined bucket.
    This function is intended to be used in a Pool of workers.

    :param key: cloud storage key of tiff file to download and convert to jpeg
    :return str: name of file uploaded
    """
    s3 = get_s3_client()
    with TemporaryFile(dir=TEMP_DIRECTORY) as temp_tiff_file:
        s3.download_fileobj(
            Bucket=DESTINATION_BUCKET,
            Key=key,
            Fileobj=temp_tiff_file
        )
        temp_tiff_file.seek(0)

        logger.info('converting %s to jpeg', key)

        temp_jpeg = BytesIO()
        with Image(file=temp_tiff_file) as img:
            img.format = 'jpeg'
            img.save(file=temp_jpeg)

        key = re.sub(r'\.\w+$', '.jpg', key)
        s3.put_object(
            Bucket=DESTINATION_BUCKET,
            Key=key,
            Body=temp_jpeg.getvalue()
        )
        return key


def convert_tiff_images_in_expanded_bucket_to_jpeg_images(**context) -> List[str]:
    zip_file_name = get_file_name_passed_to_dag_run_conf_file(context)
    prefix = re.sub(r'\.\w+$', '/', zip_file_name)
    tiffs = {key
             for key in list_bucket_keys_iter(Bucket=DESTINATION_BUCKET, Prefix=prefix)
             if key.endswith('.tif')}

    thread_options = {
        'max_workers': WORKERS,
        'thread_name_prefix': 'converting_tiffs_%s_' % zip_file_name
    }
    with ThreadPoolExecutor(**thread_options) as p:
        uploaded_images = p.map(convert_image_in_s3_to_jpeg, tiffs)
        return list(uploaded_images)


# schedule_interval is None because DAG is only run when triggered
dag = DAG('process_zip_dag',
          default_args=default_args,
          schedule_interval=None)

extract_zip_files = create_node_task(
    name='extract_archived_files_to_bucket',
    js_task_script_path='${AIRFLOW_HOME}/dags/js/tasks/extract-archived-files-to-bucket.js',
    dag=dag
)

convert_tiff_images = python_operator.PythonOperator(
    task_id='convert_tiff_images_in_expanded_bucket_to_jpeg_images',
    provide_context=True,
    python_callable=convert_tiff_images_in_expanded_bucket_to_jpeg_images,
    dag=dag
)

get_jats_article = create_node_task(
    name='get_jats_article',
    js_task_script_path='${AIRFLOW_HOME}/dags/js/tasks/get-jats-article.js',
    dag=dag
)

update_tiff_references = create_node_task(
    name='update_tiff_references_to_jpeg_in_article',
    js_task_script_path='${AIRFLOW_HOME}/dags/js/tasks/update-tiff-references-to-jpeg-in-article.js',
    dag=dag,
    get_return_from='get_jats_article'
)

add_missing_jpeg_extensions = create_node_task(
    name='add_missing_jpeg_extensions_in_article',
    js_task_script_path='${AIRFLOW_HOME}/dags/js/tasks/add-missing-jpeg-extensions-in-article.js',
    dag=dag,
    get_return_from='update_tiff_references_to_jpeg_in_article'
)

strip_related_article_tags = create_node_task(
    name='strip_related_article_tags_from_article_xml',
    js_task_script_path='${AIRFLOW_HOME}/dags/js/tasks/strip-related-article-tags.js',
    dag=dag,
    get_return_from='add_missing_jpeg_extensions_in_article'
)

strip_object_id_tags = create_node_task(
    name='strip_object_id_tags_from_article_xml',
    js_task_script_path='${AIRFLOW_HOME}/dags/js/tasks/strip-object-id-tags.js',
    dag=dag,
    get_return_from='strip_related_article_tags_from_article_xml'
)

add_missing_uri_schemes = create_node_task(
    name='add_missing_uri_schemes',
    js_task_script_path='${AIRFLOW_HOME}/dags/js/tasks/add-missing-uri-schemes.js',
    dag=dag,
    get_return_from='strip_object_id_tags_from_article_xml'
)

wrap_article = create_node_task(
    name='wrap_article_in_libero_xml',
    js_task_script_path='${AIRFLOW_HOME}/dags/js/tasks/wrap-article-in-libero-xml.js',
    dag=dag,
    get_return_from='add_missing_uri_schemes'
)

send_article = create_node_task(
    name='send_article_to_content_service',
    js_task_script_path='${AIRFLOW_HOME}/dags/js/tasks/send-article-to-content-service.js',
    dag=dag,
    get_return_from='wrap_article_in_libero_xml'
)

reindex_search = create_node_task(
    name='send_post_request_to_reindex_search_service',
    js_task_script_path='${AIRFLOW_HOME}/dags/js/tasks/send-post-request-to-reindex-search-service.js',
    dag=dag
)


# set task run order

# branch 1
extract_zip_files.set_downstream(convert_tiff_images)
convert_tiff_images.set_downstream(send_article)

# branch 2
extract_zip_files.set_downstream(get_jats_article)
get_jats_article.set_downstream(update_tiff_references)
update_tiff_references.set_downstream(add_missing_jpeg_extensions)
add_missing_jpeg_extensions.set_downstream(strip_related_article_tags)
strip_related_article_tags.set_downstream(strip_object_id_tags)
strip_object_id_tags.set_downstream(add_missing_uri_schemes)
add_missing_uri_schemes.set_downstream(wrap_article)
wrap_article.set_downstream(send_article)

# join
send_article.set_downstream(reindex_search)
