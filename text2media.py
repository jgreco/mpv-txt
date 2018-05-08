#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, sys,os
from subprocess import call, check_output

#shamelessly ripped/adapted from https://stackoverflow.com/questions/4576077/python-split-text-on-sentences/31505798#31505798
#this could be made a lot better
def split_into_sentences(text):
    caps = "([A-Z])"
    digits = "([0-9])"
    prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
    suffixes = "(Inc|Ltd|Jr|Sr|Co)"
    starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
    acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
    websites = "[.](com|net|org|io|gov)"

    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + caps + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(caps + "[.]" + caps + "[.]" + caps + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(caps + "[.]" + caps + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + caps + "[.]"," \\1<prd>",text)
    text = re.sub(digits + "[.]" + digits,"\\1<prd>\\2",text)
    if "”" in text: text = text.replace(".”","”.")
    if ")" in text: text = text.replace(".)",").")
    if "]" in text: text = text.replace(".]","].")
    if "'" in text: text = text.replace(".'","'.")
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences

if len(sys.argv) != 3:
    sys.exit("wrong args: text2media.py project-name input.txt")
project=sys.argv[1]
in_file=sys.argv[2]
project_dir="/tmp/mpv-txt/"+project
os.makedirs(project_dir, exist_ok=True)

def say(text):
    #try `say` first because quality is better, fall back on `espeak`
    try:
        call(["say", "..."+text, "-o", project_dir+"/tts.aiff"])
        return project_dir+"/tts.aiff"
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            try:
                call(["espeak", "-w", project_dir+"/tts.wav", "..."+text ])
                return project_dir+"/tts.wav"
            except OSError as e:
                if e.errno == os.errno.ENOENT:
                    sys.exit("text2media.py requires either `say` (OSX) or `espeak` to be in your PATH.")
                else:
                    raise
            else:
                raise


def text_to_mp4(text, fragment):
    out=project_dir+"/"+project+"-"+str(fragment)+".mp4"
    if os.path.isfile(out):
        return
    #create TTS audio
    audio_file = say(text)

    #create SRT
    try:
        audio_len = check_output([
            "ffprobe",
            "-v", "quiet",
            "-show_entries",  "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            "-sexagesimal",
            audio_file]).decode("utf-8").rstrip()
        audio_len = re.match("(\d+:\d+:\d+\.\d{1,2})", audio_len).group(1)
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            sys.exit("text2media.py requires ffprobe (from ffmpeg) to be in your PATH.")
        else:
            raise

    with open(project_dir+"/tts.srt", "w+") as srt:
        srt.write("1\n")
        srt.write("00:00:00.000 --> " + audio_len + "\n")
        srt.write(text)
    
    #combine srt and tts audio as an mp4
    try:
        call(["ffmpeg", "-v", "quiet",
            "-i", audio_file,
            "-i",  project_dir+"/tts.srt",
            "-c:a", "mp3", "-c:s", "mov_text", out])
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            sys.exit("text2media.py requires ffmpeg to be in your PATH.")
        else:
            raise

    #add sentence mp4 to the fragment list
    with open(project_dir+"/fragments.txt", "a+")  as fragments:
        fragments.write("file '"+out+"'\n")


def combine_fragments():
    out=project_dir+"/"+project+".mp4"
    if os.path.isfile(out):
        return out
    try:
        call(["ffmpeg", "-v", "quiet",
            "-safe", "0",
            "-f", "concat",
            "-i", project_dir+"/fragments.txt",
            "-c", "copy",
            "-c:s", "mov_text",
            out])
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            sys.exit("text2media.py requires ffmpeg to be in your PATH.")
        else:
            raise
    return out 

file_text = open(in_file,encoding='utf-8').read()+"."
sentences = split_into_sentences(file_text)
for i,s in enumerate(sentences):
    text_to_mp4(s, i)
print(combine_fragments())
