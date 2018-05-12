install:
	cp txt_hook.lua ~/.config/mpv/scripts/
	cp text2media.py ~/.config/mpv/
	chmod +x ~/.config/mpv/text2media.py

test:
	mpv moby\ dick\ \(c1\).txt

test-clean:
	rm -rf /tmp/mpv-txt/moby\ dick\ \(c1\)
