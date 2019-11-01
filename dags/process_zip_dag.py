"""
DAG processes a zip file stored in an AWS S3 bucket and prepares the extracted xml
file for Libero content API and sends to the content store via a PUT request.
"""
import logging
from datetime import timedelta

from airflow import DAG
from airflow.utils import timezone

from libero.operators import create_node_task

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


# schedule_interval is None because DAG is only run when triggered
dag = DAG('process_zip_dag',
          default_args=default_args,
          schedule_interval=None)

extract_zip_files = create_node_task(
    name='extract_archived_files_to_bucket',
    js_task_script_path='${AIRFLOW_HOME}/dags/js/tasks/extract-archived-files-to-bucket.js',
    dag=dag
)

convert_tiff_images = create_node_task(
    name='convert_tiff_images_in_expanded_bucket_to_jpeg_images',
    js_task_script_path='${AIRFLOW_HOME}/dags/js/tasks/convert-tiff-images-in-expanded-bucket-to-jpeg-images.js',
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
