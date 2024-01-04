import traceback
from mastodon import Mastodon
from tenacity import retry, stop_after_attempt, retry_if_result
from utils.globals import log, cfg, CAT_TAGS

@retry(stop=stop_after_attempt(3), retry = retry_if_result(lambda result: result is False))
async def post_mastodon(post, job_id):
	# Mastodon API client
	mstdn: Mastodon = ""

	try:
		mstdn = Mastodon(
			client_id = cfg.get('mastodon.client_id'),
			client_secret = cfg.get('mastodon.client_secret'),
			access_token = cfg.get('mastodon.access_token'),
			api_base_url = cfg.get('mastodon.api_url')
		)
	except:
		log.error(f"An error occurred while initializing the Mastodon API client\n{traceback.format_exc()}")
		return

	# Assign the post data to individual variables in order to make accessing the properties easier
	caption = post.get('caption', '')
	alt_text = post.get('alt_text', '')
	emoji = post.get('emoji', '')
	catbox_url = post.get('catbox_url', '')


	# Post to mastodon
	media = mstdn.media_post(f"jobs/{job_id}.gif", mime_type = "image/gif", description=alt_text)

	hasFinishedProcessing = False
	while not hasFinishedProcessing:
		res = mstdn.media(media['id'])
		if res.get('url', None) is not None:
			hasFinishedProcessing = True

	post = mstdn.status_post(
		status = caption,
		media_ids = [media]
	)

	mstdn.status_post(
		status = f"{catbox_url} - {emoji}",
		in_reply_to_id = post["id"]
	)

	if post.get('url', None) is None:
		log.error(f"An error occurred while posting to Mastodon\n{post}")
		return False

	log.success(f'Successfully posted to Mastodon! {post["url"]}')
	return post['url']