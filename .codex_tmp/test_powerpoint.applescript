set outPath to "/Users/korrenhannes/Documents/GitHub/diffintent-rtl/.codex_tmp/test_powerpoint.pptx"

tell application "Microsoft PowerPoint"
	activate
	set p to make new presentation
	delay 1
	-- New PowerPoint presentations use the widescreen 16:9 default.
	set s to make new slide at end of active presentation
	set layout of s to slide layout blank
	set bg to make new text box at end of s with properties {left position:0, top:0, width:960, height:540}
	solid (fill format of bg)
	set fore color of fill format of bg to {246, 247, 251}
	set transparency of line format of bg to 1
	set tb to make new text box at end of s with properties {left position:80, top:90, width:800, height:100}
	set content of text range of text frame of tb to "בדיקת מצגת RTL"
	set font name of font of text range of text frame of tb to "Arial"
	set font size of font of text range of text frame of tb to 34
	set bold of font of text range of text frame of tb to true
	set font color of font of text range of text frame of tb to {11, 31, 51}
	set alignment of paragraph format of text range of text frame of tb to paragraph align right
	set text direction of paragraph format of text range of text frame of tb to right to left
	set noteSlide to notes page of s
	set content of text range of text frame of shape 2 of noteSlide to "00:20 | הערת דובר לבדיקה"
	save p in outPath as save as Open XML presentation
	close p saving no
end tell
