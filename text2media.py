#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, sys, os, argparse, shutil, errno
from subprocess import call, check_output
from multiprocessing import Pool, Process, Queue
from queue import Empty

progressQ = Queue()

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

    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")

    if "”" in text: text = text.replace(".”","”.")
    if "”" in text: text = text.replace("!”","”!")
    if "”" in text: text = text.replace("?”","”?")

    if ")" in text: text = text.replace(".)",").")
    if ")" in text: text = text.replace("!)",")!")
    if ")" in text: text = text.replace("?)",")?")

    if "]" in text: text = text.replace(".]","].")
    if "]" in text: text = text.replace("!]","]!")
    if "]" in text: text = text.replace("?]","]?")

    if "'" in text: text = text.replace(".'","'.")
    if "'" in text: text = text.replace("!'","'!")
    if "'" in text: text = text.replace("?'","'?")

    text = text.replace(".",".<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences

calibre_install_locations = [
        "/Applications/calibre.app/Contents/MacOS/ebook-convert",
        "~/Applications/calibre.app/Contents/MacOS/ebook-convert"]
#convert ebook to txt:
#  various formats supported: https://manual.calibre-ebook.com/generated/en/ebook-convert.html
def ebook_convert(ebook):
    out = project+"/"+basename+".txt"
    try:
        call(["ebook-convert", ebook, out],
                stdout=open(os.devnull, 'w'))
    except OSError as e:
        if e.errno == errno.ENOENT:
            calibre_installs = [f for f in calibre_install_locations if os.path.isfile(f)]
            if not calibre_installs:
                sys.exit("text2media.py could not find `ebook-convert`. Make sure you have Calibre (https://calibre-ebook.com/) installed and `ebook-convert` in your path.")

            call([calibre_installs[0], ebook, out],
                    stdout=open(os.devnull, 'w'))
        else:
            raise

    if args.editor_cleanup:
        call(["xterm", "-e", os.environ.get('EDITOR', 'nano') + " " + out])

    return out


#try `say` first because quality is better, fall back on `espeak`
def say(text,fragment):
    try:
        out = project+"/tts-"+str(fragment)+".aiff"
        call(["say", "..."+text, "-o", out])
        return out
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            try:
                out = project+"/tts-"+str(fragment)+".wav"
                call(["espeak", "-w", out, "..."+text ])
                return out
            except OSError as e:
                if e.errno == os.errno.ENOENT:
                    sys.exit("text2media.py requires either `say` (OSX) or `espeak` to be in your PATH.")
                else:
                    raise
        else:
            raise


def text_to_mp4(fragment_text):
    fragment = fragment_text[0]
    text = fragment_text[1]
    out=project+"/"+basename+"-"+str(fragment)+".mp4"

    if os.path.isfile(out):
        if args.gui_progressbar:
            progressQ.put(True)
        return out

    #create TTS audio
    audio_file = say(text, fragment)

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

    srt_file = project+"/tts-"+str(fragment)+".srt"
    with open(srt_file, 'w+', encoding='utf-8') as srt:
        srt.write("1\n")
        srt.write("00:00:00.000 --> " + audio_len + "\n")
        srt.write(text)
    
    #combine srt and tts audio as an mp4
    try:
        call(["ffmpeg", "-v", "quiet",
            "-i", audio_file,
            "-i",  srt_file,
            "-c:a", "mp3", "-c:s", "mov_text", out])
        os.remove(srt_file)
        os.remove(audio_file)
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            sys.exit("text2media.py requires ffmpeg to be in your PATH.")
        else:
            raise

    if args.gui_progressbar:
        progressQ.put(True)

    if not os.path.isabs(project):
        return basename+"-"+str(fragment)+".mp4"
    return out

def combine_fragments(fragments):
    out = args.output if args.output else project+"/"+basename+".mp4"
    if os.path.isfile(out):
        return out

    with open(project+"/fragments.txt", 'w', encoding='utf-8') as fragment_list:
        for f in fragments:
            fragment_list.write("file '%s'\n" % f)
    try:
        call(["ffmpeg", "-v", "quiet",
            "-safe", "0",
            "-f", "concat",
            "-i", project+"/fragments.txt",
            "-c", "copy",
            "-c:s", "mov_text",
            out])
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            sys.exit("text2media.py requires ffmpeg to be in your PATH.")
        else:
            raise
    return out 

ap = argparse.ArgumentParser()
ap.add_argument("input_file", type=str, help="text file to process")
ap.add_argument("-t", "--threads", type=int, default=1, help="number of threads to use for TTS")
ap.add_argument("-o", "--output", type=str, help="specify the output path/name")
ap.add_argument("-p", "--project_directory", type=str, help="override the project directory (defaults to a new directory in /tmp/mpv-txt/ )")
ap.add_argument("-x", "--cleanup", action="store_true", help="cleanup all intermediate product files before exiting")
ap.add_argument("-e", "--editor-cleanup", action="store_true", help="launch a text editor to clean up Calibre output")
ap.add_argument("-g", "--gui-progressbar", action="store_true", help="display a GUI progress bar")
args = ap.parse_args()

basename = os.path.basename(os.path.splitext(args.input_file)[0])
project = args.project_directory if args.project_directory else "/tmp/mpv-txt/"+basename
os.makedirs(project, exist_ok=True)

if os.path.splitext(args.input_file)[1] != ".txt":
    args.input_file = ebook_convert(args.input_file)

file_text = open(args.input_file,encoding='utf-8').read()+"."
sentences = split_into_sentences(file_text)

def generate():
    with Pool(args.threads) as pool:
        fragments = pool.map(text_to_mp4, [(i,s) for i,s in enumerate(sentences)])

    result = combine_fragments(fragments)
    if args.gui_progressbar:
        progressQ.put(False)
    print(result)

if args.gui_progressbar:
    from tkinter import *
    from tkinter import ttk

    root = Tk()
    root.title("mpv-txt: %s" % basename)
    root.resizable(False, False)
    root.attributes("-topmost", True)

    txt = Label(root, text="processing fragments (%d of %d)" % (0, len(sentences)))
    txt.pack()

    pb = ttk.Progressbar(root, orient="horizontal", length=400, maximum=len(sentences), mode="determinate")
    pb.pack()

    gen = Process(target=generate)
    gen.start()

    def update():
        while True:
            try:
                m = progressQ.get_nowait()
                if m:
                    pb["value"] = pb["value"] + 1
                    txt["text"] = "processing fragments (%d of %d)" % (pb["value"], len(sentences))
                    if pb["value"] == len(sentences):
                        txt["text"] = "combining fragments..."
                else:
                    root.quit()
                    root.update()
            except Empty:
                break
            except:
                raise
        root.after(100, update)

    root.after(0, update)
    root.mainloop()
else:
    generate()

if args.cleanup:
    if not os.path.split(result)[0].startswith(project):
        shutil.rmtree(project)
    else:
        for f in os.listdir(project):
            if f != os.path.split(result)[1]:
                os.remove(project+"/"+f)
