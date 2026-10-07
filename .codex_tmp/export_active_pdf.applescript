set posixPath to "/Users/korrenhannes/Documents/GitHub/diffintent-rtl/.codex_tmp/final_deck_v18.pdf"
set hfsPath to (POSIX file posixPath) as text
tell application "Microsoft PowerPoint"
	set p to active presentation
	save p in hfsPath as save as PDF
	delay 5
end tell
