set targetPosix to "/Users/korrenhannes/Documents/GitHub/diffintent-rtl/report/DiffIntent_RTL_Final_Presentation_Hebrew.pptx"
set backupPosix to "/Users/korrenhannes/Documents/GitHub/diffintent-rtl/.codex_tmp/open_final_before_reload_v16.pptx"
set targetPath to (POSIX file targetPosix) as text
set backupPath to (POSIX file backupPosix) as text

tell application "Microsoft PowerPoint"
	set p to presentation "DiffIntent_RTL_Final_Presentation_Hebrew.pptx"
	save p in backupPath as save as Open XML presentation
	close p saving no
	open targetPath
	delay 4
	activate
end tell
