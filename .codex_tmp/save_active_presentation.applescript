set outPath to "/Users/korrenhannes/Documents/GitHub/diffintent-rtl/.codex_tmp/final_deck.pptx"
tell application "Microsoft PowerPoint"
	set p to active presentation
	save p in outPath as save as Open XML presentation
	delay 5
	return full name of p
end tell
