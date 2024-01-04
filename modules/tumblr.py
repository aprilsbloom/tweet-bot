import pytumblr
import traceback
from tenacity import retry, stop_after_attempt, retry_if_result
from utils.globals import log, cfg, CAT_HASHTAGS

@retry(stop=stop_after_attempt(3), retry = retry_if_result(lambda result: result is False))
async def post_tumblr(post, job_id):
	# Tumblr API client
	tmblr: pytumblr.TumblrRestClient = ""

	try:
		tmblr = pytumblr.TumblrRestClient(
			cfg.get('tumblr.consumer_key'),
			cfg.get('tumblr.consumer_secret'),
			cfg.get('tumblr.oauth_token'),
			cfg.get('tumblr.oauth_secret')
		)
	except:
		log.error(f"An error occurred while initializing the Tumblr API client\n{traceback.format_exc()}")
		return

	# Assign the post data to individual variables in order to make accessing the properties easier
	caption = post.get('caption', '')
	alt_text = post.get('alt_text', '')
	emoji = post.get('emoji', '')
	catbox_url = post.get('catbox_url', '')

	newCaption = ''
	if caption != '':
		newCaption = f"{caption} <br><br>"

	newCaption += f'<strong>Alt text:</strong> {alt_text} <br><br><strong>Gif URL:</strong> {catbox_url} <br><br><strong>Posted by:</strong> {emoji}'


	# Post to tumblr
	blog_name = cfg.get('tumblr.blog_name')
	res = tmblr.create_photo(
		caption = newCaption,
		tags = [f'posted-by-{emoji}'] + CAT_HASHTAGS,
		data = f"jobs/{job_id}.gif",
		state = 'published',
		blogname = blog_name,
		slug = job_id
	)

	if res.get('id', None) is None:
		log.error(f"An error occurred while posting to Tumblr\n{res}")
		return False

	log.success(f'Successfully posted to Tumblr! https://{blog_name}.tumblr.com/post/{res["id"]}')
	return f'https://{blog_name}.tumblr.com/post/{res["id"]}'