tell application "Microsoft PowerPoint"
	set p to make new presentation
	delay 1
	set s to make new slide at end of active presentation
	set layout of s to slide layout blank
	set n to notes page of s
	set reportText to "count=" & (count shapes of n)
	repeat with i from 1 to count shapes of n
		set sh to shape i of n
		set reportText to reportText & return & i & ": " & (name of sh) & ", type=" & (shape type of sh as text)
		try
			set reportText to reportText & ", placeholder=" & (placeholder type of sh as text)
		end try
		try
			set reportText to reportText & ", text=" & (content of text range of text frame of sh)
		end try
	end repeat
	return reportText
end tell
