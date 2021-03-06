# mpv-txt
A script for the MPV media player that allows you to play text files and ebooks using [text-to-speech (TTS)](https://en.wikipedia.org/wiki/Speech_synthesis).  
Currently supported TTS engines are `say` (MacOS) and [`espeak`](https://en.wikipedia.org/wiki/ESpeakNG).  Supported formats are txt, epub, mobi, azw3, azw4, pdf, docx, odt, [and many more.](https://manual.calibre-ebook.com/generated/en/ebook-convert.html)

![screenshot](mpv-shot0001.jpg)

## Dependancies
- MacOS, Linux, \*BSD, etc  **(Windows is NOT currently supported)**
- [python3](http://docs.python-guide.org/en/latest/starting/installation/)
- ffmpeg
- [espeak](https://en.wikipedia.org/wiki/ESpeakNG) *(not required on MacOS)*
- [Calibre](https://calibre-ebook.com/) *(OPTIONAL: only required for ebook support)*

## Installation
    make install
or:

    cp txt_hook.lua ~/.config/mpv/scripts/
    cp text2media.py ~/.config/mpv/
    chmod +x ~/.config/mpv/text2media.py
optional:

	cp txt_hook.conf ~/.config/mpv/lua-settings/

## Technical Details
*mpv-txt* works by splitting the input file into individual sentences, creating a TTS audio file from each sentence, generating an SRT subtitle file from each sentence, then using ffmpeg to combine those audio and SRT files into one mp4 per sentence *(there is no video stream)*.  Then ffmpeg is again used to combine all the per-sentence mp4 files into a single mp4.  All resulting mp4 files will be located in `/tmp/mpv-txt/`.

If the input file is an ebook, it is first run through the [`ebook-convert`](https://manual.calibre-ebook.com/generated/en/ebook-convert.html) tool from Calibre to create a text document.

The output for a reasonably average book weighs in at around 100MB.  On modest processors, [a large book like Moby Dick](http://commonplacebook.com/art/books/word-count-for-famous-novels/) may take an hour to run through TTS (Moby Dick takes about 30 minutes on my 1.6GHz i5, using MacOS's `say` and threads=4 and produces a 174MB mp4).  If the product files are still present in `/tmp/mpv-txt/` then *mpv-txt* will not regenerate them.  However you may want to copy the final product mp4 out of `/tmp/mpv-txt/` and store it someplace more permanent, so you don't need to waste your time recreating it in the future.

If you quit MPV while *mpv-txt* is in the middle of processing a file, the next time you try to play that file *mpv-txt* will resume where you left off.

## Plans For Future Enhancement
*(some of these plans may prove to be mutually exclusive)*
- [x] ~~epub/mobi support (using [Calibre's](https://en.wikipedia.org/wiki/Calibre_(software)) `ebook-convert` to generate a text file)~~
- [ ] give attention to subtitle formatting (currently all default settings are used)
- [ ] add a text substitution feature, allowing users to manipulate TTS pronounciations of difficult words
- [x] ~~parallel TTS~~
- [ ] remove python3 dependancy(?)
- [ ] windows support (low priority, but reasonable pull requests are welcome ;) )
- [ ] support for 'cloud' TTS services (VERY low priority)
