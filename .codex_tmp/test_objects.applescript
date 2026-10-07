set imgPath to "/Users/korrenhannes/Library/Containers/com.microsoft.Powerpoint/Data/tmp/diffintent_ppt_assets/figure_dataset_overview.png"
tell application "Microsoft PowerPoint"
	set p to active presentation
	set s to slide 1 of p
	set pic to make new picture at end of s with properties {file name:imgPath, link to file:false, save with document:true, left position:80, top:100, width:400, height:250}
	set ln to make new line shape at end of s with properties {begin line X:100, begin line Y:400, end line X:800, end line Y:400}
	set fore color of line format of ln to {31, 111, 235}
	set line weight of line format of ln to 3
	set end arrowhead style of line format of ln to triangle arrowhead
	return "w=" & slide width of page setup of p & ", shapes=" & (count shapes of s)
end tell
