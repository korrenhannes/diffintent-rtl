property deckPath : "/Users/korrenhannes/Documents/GitHub/diffintent-rtl/.codex_tmp/test_save_property.pptx"
tell application "Microsoft PowerPoint"
	set p to make new presentation
	delay 1
	set s to make new slide at end of p
	save p in (my deckPath) as save as Open XML presentation
	delay 2
	return full name of p
end tell
