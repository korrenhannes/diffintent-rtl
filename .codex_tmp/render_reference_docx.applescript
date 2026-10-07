set sourcePath to POSIX file "/Users/korrenhannes/Documents/GitHub/diffintent-rtl/example of good format/lecture3_deep_learning.docx" as text
set pdfPath to POSIX file "/Users/korrenhannes/Documents/GitHub/diffintent-rtl/.codex_tmp/lecture3_deep_learning_reference.pdf" as text

tell application "Microsoft Word"
	activate
	with timeout of 300 seconds
		open sourcePath
		repeat 50 times
			if (count documents) > 0 then exit repeat
			delay 0.2
		end repeat
		set d to document 1
		save as d file name pdfPath file format format PDF
		close d saving no
	end timeout
end tell
