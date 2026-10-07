set posixPath to "/Users/korrenhannes/Documents/GitHub/diffintent-rtl/.codex_tmp/test_save_hfs.pptx"
set hfsPath to (POSIX file posixPath) as text
tell application "Microsoft PowerPoint"
	set p to make new presentation
	delay 1
	set s to make new slide at end of p
	save p in hfsPath as save as Open XML presentation
	delay 2
	return full name of p
end tell
