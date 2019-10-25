
module.exports = {
  ARTICLE: '/article',
  ARTICLE_ID_BY_PUBLISHER_ID: '/article/front/article-meta/article-id[@pub-id-type="publisher-id"]',
  ARTICLE_ID_NOT_BY_PMID_PMC_DOI: '/article/front/article-meta/article-id[not(@pub-id-type="pmid") and not(@pub-id-type="pmc") and not(@pub-id-type="doi")]',
  ARTICLE_ID_BY_ELOCATION_ID: '/article/front/article-meta/elocation-id',
  ARTICLE_ID_BY_DOI: '/article/front/article-meta/article-id[@pub-id-type="doi"]',
  CATEGORIES_BY_SUBJECT_GROUP: '//article//article-meta//article-categories/subj-group[not(@subj-group-type="heading")]/subject[1]',
  IMAGE_BY_TIFF_MIMETYPE: '//*[@mimetype="image" and @mime-subtype="tiff"]',
  IMAGE_BY_JPEG_MIMETYPE: '//*[@mimetype="image" and @mime-subtype="jpeg"]',
  OBJECT_ID: '//object-id',
  RELATED_ARTICLE: '//related-article',
};
