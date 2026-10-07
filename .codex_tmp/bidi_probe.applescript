set pptxPath to (POSIX file "/Users/korrenhannes/Documents/GitHub/diffintent-rtl/.codex_tmp/bidi_probe.pptx") as text
set pdfPath to (POSIX file "/Users/korrenhannes/Documents/GitHub/diffintent-rtl/.codex_tmp/bidi_probe.pdf") as text

tell application "Microsoft PowerPoint"
	activate
	set p to make new presentation
	set s to make new slide at end of p
	set layout of s to slide layout blank
	set tb to make new text box at end of s with properties {left position:100, top:120, width:760, height:160}
	set tf to text frame of tb
	set content of text range of tf to "המודל TF-IDF השיג Macro-F1 של 0.4197, ואילו Hierarchical Transformer השיג Hole F1 של 0.6029."
	set word wrap of tf to true
	set tr to text range of tf
	set font name of font of tr to "Arial"
	set font name other of font of tr to "David"
	set font size of font of tr to 30
	set alignment of paragraph format of tr to paragraph align right
	set text direction of paragraph format of tr to right to left
	save p in pptxPath as save as Open XML presentation
	save p in pdfPath as save as PDF
end tell
