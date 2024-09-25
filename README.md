> This project, created in 2021 as part of the CS50 course, was my first attempt at building a web app. It may not be up to date or work properly, but it reflects my early learning experience.

<hr>

# LISTEN UP!

Listen Up is a website where you can practice English and improve listening skills!

> This was my CS50 final project!

> *Note: You need a YouTube API to run flask code!*

## Video Demo:  https://youtu.be/kEaZTFt7YQI

<hr>

## Background:

In my opinion English is currently the most important language to know. Of course that depends on where you live, what your needs and interests are, but in general it's better to learn English. There are tons of websites and apps we can use to make this learning process easier and fun. In [Voscreen](https://www.voscreen.com) users can watch a random movie clip and try to find which one of the two translations is correct. It's such a fun and good idea so I thought I should do something similar (and much more simpler) for my final project. However I got overwhelmed quickly by the idea of getting those movie clips while being cautious about copyright issues. Then I've changed my mind and decided to use YouTube videos instead, so I've started reading about YouTube API (which is not fun, by the way) !

## What it Does:

> Since the actual code is really messy and contains commented out parts, note to self's and some implementing options, I thought I should explain the important parts here.


#### Using an Account

Users have to create an account to use this website. Then they can change their passwords or delete their accounts.

*Note: There are no password requirements because this is a pretty simple website and it would be annoying to find a strong password for it.*

##### How it Works:

I was actually trying to do everything by myself at first; reading about sessions, requests, responses, password hashing... Then I thought if it's OK to use pset distribution code for some parts. After some googling turns out it's [perfectly fine](https://www.reddit.com/r/cs50/comments/a2w94r/comment/eb1sajj/?utm_source=share&utm_medium=web2x&context=3)! So I've based my website on Finance pset and even though I don't really know how some functions really works under the hood, I am using them.

#### Getting the YouTube video

![Imgur Image](https://imgur.com/a/F82aj17.gif)

(image link: https://imgur.com/a/F82aj17)

On the "Play" page, users can select a difficulty. Easy picks a random [TED-Ed](https://www.youtube.com/teded) video, Normal picks a [Kurzgesagt](https://www.youtube.com/c/inanutshell/) video and Hard picks a [Minute Earth](https://www.youtube.com/c/minuteearth) video, since they usually speak faster in their videos. Then algorithm selects a random part of that video and plays it to the user. If they type the sentence correctly then they get 1-2-3 points, depending on the difficulty.

##### How it Works:

Even though I've played around a lot with the code samples in the [documentation](https://developers.google.com/youtube/v3/docs/channels/list), I couldn't really achieve what I had in mind. The json file they required wasn't working. So I had to make it simple and go step by step;
```python
# (function call with the channel URL)
# Get a bunch of video of the given channel:
url = f"https://www.googleapis.com/youtube/v3/search?order=date&part=snippet&channelId={channel}&maxResults=50&key={api_key}"
response = requests.get(url)

# The response is quite messy! This is how I get a single url:
videos = response.json()
video = videos['items'][0]['id']['videoId']
# to get a random video:
video = videos['items'][randomnumber]['id']['videoId']
```

So I have the URL of a random video of the channel, but I still need the transcript.

```python
# (function call with the video URL)
# Get the English transcript:
url = f"http://video.google.com/timedtext?lang=en&v={video}"
response = requests.get(url)

# If transcript (string) contains 50 or less characters, we should try another video!
if len(response.text) < 50:
    return None
```

After using this code for some time, I've noticed some videos doesn't have "English" subtitles per se, but they have "English (United Kingdom)" subtitles and this is causing the algorithm to pick another video. So I've modified the code:

```python
if len(response.text) < 50:
    # let's try to get UK subtitles. Notice "lang=en-GB" this time.
    url = f"http://video.google.com/timedtext?lang=en-GB&v={video}"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        print("Something went wrong...")
        return None

    # IF still no caption, then return none.
    if len(response.text) < 50:
        return None
```

However this was still the wrong approach. There are a lot of English based subtitles, not just "en" and "en-GB". I should just request the list of available languages and check if it contains anything English based. But for now I feel like this is enough since these 3 channels mostly have en or en-GB subtitles. I'll optimize this function later when I add more channels as an option.

```bash
# print(response.text)

<?xml version="1.0" encoding="utf-8" ?><transcript><text start="0.94" dur="3.76">What would happen if you were to bring
a tiny piece of the Sun to Earth?</text><text start="4.72" dur="5.42">Short answer: you die.
Long answer: it depends which piece of the Sun.</text><text start="10.42" dur="6.48">Like most of the matter in the universe,
our Sun is neither solid, liquid or gas, but plasma.
```

Now all I have to do is cleaning the transcript from HTML tags. I've done little bit of searching, most of the people thinks using regex to clean HTML tags is a bad idea but since this is a relatively simple task, I thought it's OK to use regex.

```python
try:
    substr = re.findall(r"<text(.*?)</text>", response.text)
except Exception as e:
    print(e)
    return None

# But of course those people were right.
# While regex usually does a good job, sometimes it creates and empty list and causing problems.
# So I've add the following, just in case regex fails.

if not substr:
    # source: https://stackoverflow.com/a/19772902
    rand = max(random.randint(0, response.text.count("<text")), 3)

    sentence = response.text.split('<text', rand)[rand-1]
    if sentence.endswith('</text>'):
        sentence = sentence[:-7]
else:
    sentence = random.choice(substr)
```

In the end, I am ending up with sentence string, which looks something like this:

```bash
# print(sentence)

start="328.86" dur="2.8">possibly humans civilization ending.
```

Now all I have to do is getting the start value, duration and the actual subtitle; put them in a list and return:

```python
# html.unescape (from docs): Convert all named and numeric character references (e.g. &gt;, &#62;, &#x3e;) in the string s to the corresponding Unicode characters.
html.unescape(sentence)

# split the string; a contains the time info are and b contains subtitle.
a,b = sentence.split('>', maxsplit=1)
a = a.replace("\"", " ")

mylist = []

for i in a.split(' '):
    try:
        # only get the numeric values.
        result = float(i)
        mylist.append(result)
    except:
        continue

mylist.append(b)

return mylist

# mylist looks something like this:
# [245.609, 2.651, 'the temperature is 15 million degrees,']
```

And back in the first function, I am waiting for a list which contains 3 items as the return value:

```python
while True:
    rndm = random.randint(0, len(videos['items'])-1)
    video = videos['items'][rndm]
    subtitle = getCaption(video['id']['videoId'])
    if subtitle == None:
        continue
    if len(subtitle) == 3:
        break

mylist = [video['id']['videoId'], subtitle]
return mylist

# mylist looks something like this now:
# ['WA_jIj_w12U', [268.663, 3.458, 'promoting overfishing and illegal fishing.']]
# mylist[0] = video url
# mylist[1][2] = random subtitle in the video
# mylist[1][0] and mylist[1][1] = start time and duration of subtitle
```

So, 268th second of that [video](https://www.youtube.com/watch?v=WA_jIj_w12U&t=268s):

![Imgur Image](https://imgur.com/a/CkIOQXO.png)

(image link: https://imgur.com/a/CkIOQXO)

###### Summary:

* **GetVideo(channel URL):**
* Request some videos of the given channel
* Until getting the subtitle properly:
  * Pick a random video URL
  * **GetSubtitle(video URL):**
  * Request en or en-GB transcript of the given video
  * Clean the HTML tags from the transcript
  * Pick a random sentence and return it with it's time info.
* Return video URL along with the subtitle information.

These are the first functions I've implemented and I was quite proud of the result. However these need heavy optimizations if I ever think about buying a domain and host this website! Because every time the user plays the "game" I have to request the video from YouTube and this takes a lot of time. Doing this over and over again would be such a **horrible** design. Now I'm planning to make a script to save all the videos of these channels to the database; with every caption and timestamps of these captions. This way I can store tens of thousands video-caption dual (questions) easily. In fact, I can order these by the subtitle length and make a proper difficulty system. **However** these would take a lot of time to implement and I need to finish this project now. It's slow but it's working.

#### "Displaying" the Video:

```python
diffSelected = request.form.get("diff")
if not diffSelected:
    flash("You have to choose difficulty")
    return render_template("play.html")

if diffSelected == 'easy':
    # TED-Ed channel URL
    vid = callYT("UCsooa4yRKGN_zEE8iknghZA")
    pts = 1
elif diffSelected == 'normal':
    # Kurzgesagt channel URL
    vid = callYT("UCsXVk37bltHxD1rDPwtNM8Q")
    pts = 2
elif diffSelected == 'hard':
    # Minute Earth channel URL
    vid = callYT("UCeiYXex_fwgYDonaTcSIk6w")
    pts = 3
else:
    flash("Invalid option!")
    return render_template("play.html")
```

After getting the video and subtitle information, I had to find a way to return the given part (and only the given part) of video to the user. I've played around with the code for so long and tried so much libraries. I've tried python-vlc, pafy, or downloading the clip via youtube-dl and subprocess ffmpeg but I couldn't achieve what I have in mind with none of them and end up using YouTube embedded video.

```python
url = f"https://www.youtube.com/embed/{vid[0]}?start={start}&end={end}&controls=0&disablekb=1&autoplay=1&cc_load_policy=3&version=3"
```  

##### How it Works:

Now I could start and end the video where I want with the Embed URL. The problem is, now I have to prevent the user from interacting with the video. Since they can easily watch unrelated part of the video, display subtitles to cheat, or even watch completely different videos (via clicking "related videos")

```html
{% if url is defined %}
    <div class="wrapper">
        <div class="frame-container">
            <iframe src="{{ url }}" id="iframeid" allow="autoplay"></iframe>
        </div>
    </div>
{% endif %}


<script>

/*
  To let user listen the audio again, I am basically refreshing the video.
*/

var inputrefresh = document.getElementById("refreshbutton");
inputrefresh.addEventListener("click", function() {
    document.getElementById('iframeid').src += '';
});

</script>
```
```css
.frame-container {
    position: relative;
    padding-bottom: 56.25%; /* 16:9 */  
    padding-top: 25px;
    width: 300%; /* enlarge beyond browser width */
    left: -100%; /* center */
}

.frame-container iframe {
    position: absolute;
    top: 0;
    left: 0;
    width: 1%;
    height: 1%;
}

.wrapper {
    overflow: hidden;
    max-width: 100%;
}
```

After some googling, I've found [this](https://stackoverflow.com/a/60228328) elegant solution! And while playing with that code, I've noticed I can completely make the video invisible. So I've just make the width-height values 1% and voila, video was no more!

However, one **huge** problem with this whole embedded video idea is that, every time user needs to listen the audio, there will be some loading time and it's really annoying...  I have to find a better way later,  right now it's working slowly but surely!

#### Checking the User Input

After the user types what they heard, I have to compare that string with the original subtitle.

```python
# get rid of the punctuation
uinput = ''.join((c for c in uinput if c not in punctuation))
subtitle = ''.join((c for c in subtitle if c not in punctuation))

# get rid of unwanted whitespace
uinput = ' '.join(uinput.split())
subtitle = ' '.join(subtitle.split())

isTrue = 0
if subtitle.casefold() == uinput.casefold():
    isTrue = 1
```

But there was a **HUGE** problem with this approach which I didn't noticed at first. I could only start and end videos in *integer* seconds. However almost every caption has *float* time info. For example one caption would start at 15.586s second, and continue for 6.47 seconds. But I had choose to display the video from either 15th second or 16th second; and continue displaying for 6 seconds or 7 seconds. User would hear either too much or too less. Both is bad and making it basically unplayable. I've tried making complex algorithms to detect these extra words in the string, making the comparison word by word, even tried different libraries such as difflib to make similarity based system... but none of them really worked... I was frustrated and I thought even starting a new project. After some hours, I've decided to made it really simple and make sure to start the video early and end it late. That would be the safest approach to this problem.

```python
# Before sending the video, I make sure to keep it longer.
start = int(vid[1][0]) - 1
end = start + int(round(vid[1][1])) + 3
url = f"https://www.youtube.com/embed/{vid[0]}?start={start}&end={end}&controls=0&disablekb=1&autoplay=1&cc_load_policy=3&version=3"

# And while checking the result, I am simply searching the actual caption in user's answer
isTrue = 0
if subtitle.casefold() in uinput.casefold():
    isTrue = 1
```

So in general user will type 2-3 more words but it's the best solution I came up with! If I will ever find a better way to display video/audio to the user, I can definitely improve the checking system too. But right now it's the only way I can think of with embed URL. If there are still buggy videos, user can click a button and report the video as buggy (those are saved in the database).

#### History Table

![Imgur Image](https://imgur.com/a/0uql7Ea.png)

(Image link: https://imgur.com/a/0uql7Ea)

In history page, users can see all the videos (and video parts) they've answered. They can still check out the source video, see the original caption, their answer and when they answered. They can also order the table by video name, by date&time and they can search the captions & answers.

##### How it works:

All the answers are stored in the database and displayed in the basic bootstrap table with the help of jinja. All the other details are created by using a JavaScript library called [DataTables](https://datatables.net).

```html
<script type="text/javascript" charset="utf8" src="https://code.jquery.com/jquery-3.5.1.js"></script>
<script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/1.11.3/js/jquery.dataTables.min.js"></script>
<script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/1.11.3/js/dataTables.bootstrap4.min.js"></script>
<script>
    $(document).ready(function () {
      $('#historytable').DataTable({
        columns: [
            {searchable: false},
            {searchable: false, orderable: false},
            {orderable: false},
            {orderable: false},
            {searchable: false}
        ]
      });
    });
  </script>
```

#### Leaderboard

![Imgur Image](https://imgur.com/a/zm8CyOR.png)

(Image link: https://imgur.com/a/zm8CyOR)

In the leaderboard page users with top ten scores are displayed and if the current user is not in top ten, their rank and score are displayed in the last row instead

## Future plans:

I am not really satisfied with the website at the moment. I have to optimize so much before actually hosting the site. I have to save the videos in a database, instead of requesting from YouTube every time. Then I can get the videos depending on the caption length and make a proper difficulty system. I have to find a better way to display video/audio to reduce the loading time and also improve the checking system. I'll definitely need to do some front-end work and make the website pretty. I am planning to put more things on index page and actually remove the login requirement for it; it's not good to just display the login page to the first-time visitors.

But I have to finish the project now, before trying to do any of these things since they will require a lot of time and it's been already so long since I've started this course. Hope you'll like the website!
