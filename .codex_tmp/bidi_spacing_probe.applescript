property nbsp : character id 160
property lrm : character id 8206
property rlm : character id 8207
property lre : character id 8234
property pdfmark : character id 8236
property lri : character id 8294
property pdi : character id 8297

on addLine(theSlide, labelText, theText, posY)
	tell application "Microsoft PowerPoint"
		set lab to make new text box at end of theSlide with properties {left position:35, top:posY, width:90, height:46}
		set content of text range of text frame of lab to labelText
		set font size of font of text range of text frame of lab to 15
		set tb to make new text box at end of theSlide with properties {left position:135, top:posY, width:760, height:46}
		set tr to text range of text frame of tb
		set content of tr to theText
		set font name of font of tr to "Arial"
		set font name other of font of tr to "David"
		set font size of font of tr to 23
		set alignment of paragraph format of tr to paragraph align right
		set text direction of paragraph format of tr to right to left
	end tell
end addLine

tell application "Microsoft PowerPoint"
	activate
	set p to make new presentation
	set s to make new slide at end of p
	set layout of s to slide layout blank
	my addLine(s, "NBSP", "מפתח אנושי בתהליך" & nbsp & "Code" & nbsp & "Review" & nbsp & "קורא יחד את ההקשר והמבנה.", 55)
	my addLine(s, "2 NBSP", "מפתח אנושי בתהליך" & nbsp & nbsp & "Code" & nbsp & "Review" & nbsp & nbsp & "קורא יחד את ההקשר והמבנה.", 115)
	my addLine(s, "LRM", "מפתח אנושי בתהליך " & lrm & "Code Review" & lrm & " קורא יחד את ההקשר והמבנה.", 175)
	my addLine(s, "LRM+NBSP", "מפתח אנושי בתהליך" & nbsp & lrm & "Code Review" & lrm & nbsp & "קורא יחד את ההקשר והמבנה.", 235)
	my addLine(s, "LRE/PDF", "מפתח אנושי בתהליך " & lre & "Code Review" & pdfmark & " קורא יחד את ההקשר והמבנה.", 295)
	my addLine(s, "LRI/PDI", "מפתח אנושי בתהליך " & lri & "Code Review" & pdi & " קורא יחד את ההקשר והמבנה.", 355)
	my addLine(s, "RLM/LRM", "מפתח אנושי בתהליך" & rlm & " " & lrm & "Code Review" & lrm & " " & rlm & "קורא יחד את ההקשר והמבנה.", 415)
	set outPath to (POSIX file "/Users/korrenhannes/Documents/GitHub/diffintent-rtl/.codex_tmp/bidi_spacing_probe.pptx") as text
	save p in outPath as save as Open XML presentation
	delay 3
	set pdfPath to (POSIX file "/Users/korrenhannes/Documents/GitHub/diffintent-rtl/.codex_tmp/bidi_spacing_probe.pdf") as text
	save p in pdfPath as save as PDF
	delay 3
end tell
