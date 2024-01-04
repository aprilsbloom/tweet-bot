import tweepy
import traceback
from tenacity import retry, stop_after_attempt, retry_if_result
from utils.globals import log, cfg, CAT_HASHTAGS

@retry(stop=stop_after_attempt(3), retry = retry_if_result(lambda result: result is False))
async def post_twitter(post, job_id):
	# Twitter API clients
	try:
		tw_auth = tweepy.OAuth1UserHandler(
			cfg.get('twitter.consumer_key'),
			cfg.get('twitter.consumer_secret'),
			cfg.get('twitter.access_token'),
			cfg.get('twitter.access_token_secret'),
		)

		tw_v1 = tweepy.API(tw_auth, wait_on_rate_limit = True)
		tw_v2 = tweepy.Client(
			consumer_key = cfg.get('twitter.consumer_key'),
			consumer_secret = cfg.get('twitter.consumer_secret'),
			access_token = cfg.get('twitter.access_token'),
			access_token_secret = cfg.get('twitter.access_token_secret'),
			bearer_token = cfg.get('twitter.bearer_token'),
			wait_on_rate_limit = True,
		)
	except:
		log.error(f"An error occurred while initializing the Twitter API clients\n{traceback.format_exc()}")
		return


	# Assign the post data to individual variables in order to make accessing the properties easier
	caption = post.get('caption', '')
	alt_text = post.get('alt_text', '')
	emoji = post.get('emoji', '')
	catbox_url = post.get('catbox_url', '')


	# Upload gif to twitter
	mediaID = tw_v1.chunked_upload(
		filename = f"jobs/{job_id}.gif",
		media_category = "tweet_gif"
	).media_id_string

	if alt_text != "":
		tw_v1.create_media_metadata(
			media_id = mediaID,
			alt_text = alt_text
		)

	# Post tweet and reply to it with url & emoji
	tweet = tw_v2.create_tweet(
		text = caption,
		media_ids = [mediaID]
	)

	tw_v2.create_tweet(
		text = f"{catbox_url} - {emoji}",
		in_reply_to_tweet_id = tweet[0]["id"]
	)

	if tweet[0].get('id', None) is None:
		log.error(f"An error occurred while posting to Twitter\n{tweet}")
		return False

	log.success(f'Successfully posted to Twitter! https://twitter.com/i/status/{tweet[0]["id"]}')
	return f"https://twitter.com/i/status/{tweet[0]['id']}"