property navy : {11, 31, 51}
property blue : {31, 111, 235}
property orange : {245, 158, 11}
property redColor : {220, 76, 100}
property pGreen : {46, 157, 120}
property pptWhite : {255, 255, 255}
property paper : {255, 255, 255}
property paleBlue : {232, 241, 251}
property paleOrange : {255, 244, 224}
property paleGreen : {231, 247, 240}
property paleRed : {253, 235, 239}
property ink2 : {71, 84, 103}
property grayLine : {207, 214, 224}
property lri : character id 8294
property pdi : character id 8297

property assetsDir : "/Users/korrenhannes/Library/Containers/com.microsoft.Powerpoint/Data/tmp/diffintent_ppt_assets/"
set posixOutPath to "/Users/korrenhannes/Documents/GitHub/diffintent-rtl/.codex_tmp/final_deck_v18.pptx"
set outPath to (POSIX file posixOutPath) as text

on addText(theSlide, theText, posX, posY, w, h, fontSize, fontColor, isBold, alignMode, isRTL)
	tell application "Microsoft PowerPoint"
		set tb to make new text box at end of theSlide with properties {left position:posX, top:posY, width:w, height:h}
		set tf to text frame of tb
		set content of text range of tf to theText
		set word wrap of tf to true
		set vertical anchor of tf to anchor middle
		set margin left of tf to 3
		set margin right of tf to 3
		set margin top of tf to 1
		set margin bottom of tf to 1
		set tr to text range of tf
		set font name of font of tr to "Arial"
		set font name other of font of tr to "David"
		set font size of font of tr to fontSize
		set bold of font of tr to isBold
		set font color of font of tr to fontColor
		set alignment of paragraph format of tr to paragraph align center
		if isRTL then
			set text direction of paragraph format of tr to right to left
		else
			set text direction of paragraph format of tr to left to right
		end if
		return tb
	end tell
end addText

on addCode(theSlide, theText, posX, posY, w, h, fontSize, fontColor)
	tell application "Microsoft PowerPoint"
		set tb to my addText(theSlide, theText, posX, posY, w, h, fontSize, fontColor, false, "left", false)
		set font name of font of text range of text frame of tb to "Menlo"
		set font name other of font of text range of text frame of tb to "Menlo"
		set alignment of paragraph format of text range of text frame of tb to paragraph align left
		return tb
	end tell
end addCode

on addBox(theSlide, posX, posY, w, h, fillColor, borderColor, borderWidth)
	tell application "Microsoft PowerPoint"
		set b to make new shape at end of theSlide with properties {auto shape type:autoshape rectangle, left position:posX, top:posY, width:w, height:h}
		solid (fill format of b)
		set fore color of fill format of b to fillColor
		set transparency of fill format of b to 0
		set fore color of line format of b to borderColor
		set line weight of line format of b to borderWidth
		if borderWidth is 0 then set transparency of line format of b to 1
		return b
	end tell
end addBox

on addLine(theSlide, x1, y1, x2, y2, lineColor, lineWidth, arrowAtEnd)
	tell application "Microsoft PowerPoint"
		set ln to make new line shape at end of theSlide with properties {begin line X:x1, begin line Y:y1, end line X:x2, end line Y:y2}
		set fore color of line format of ln to lineColor
		set line weight of line format of ln to lineWidth
		if arrowAtEnd then set end arrowhead style of line format of ln to triangle arrowhead
		return ln
	end tell
end addLine

on addPicture(theSlide, fileNameOnly, posX, posY, w, h)
	tell application "Microsoft PowerPoint"
		return make new picture at end of theSlide with properties {file name:(assetsDir & fileNameOnly), link to file:false, save with document:true, left position:posX, top:posY, width:w, height:h}
	end tell
end addPicture

on addNotes(theSlide, noteText)
	tell application "Microsoft PowerPoint"
		set noteShape to shape 2 of notes page of theSlide
		set content of text range of text frame of noteShape to noteText
		set font name of font of text range of text frame of noteShape to "Arial"
		set font name other of font of text range of text frame of noteShape to "David"
		set font size of font of text range of text frame of noteShape to 11
		set alignment of paragraph format of text range of text frame of noteShape to paragraph align center
		set text direction of paragraph format of text range of text frame of noteShape to right to left
	end tell
end addNotes

on newSlide(thePresentation, titleText, slideLabel)
	tell application "Microsoft PowerPoint"
		set s to make new slide at end of thePresentation
		set layout of s to slide layout blank
		my addBox(s, 0, 0, 960, 540, paper, paper, 0)
		my addBox(s, 0, 0, 960, 6, blue, blue, 0)
		my addText(s, titleText, 305, 20, 607, 54, 29, navy, true, "right", true)
		my addText(s, "DiffIntent-RTL", 48, 25, 250, 30, 15, blue, true, "left", false)
		my addLine(s, 48, 74, 912, 74, grayLine, 1, false)
		my addText(s, slideLabel, 47, 500, 70, 22, 11, ink2, false, "left", false)
		return s
	end tell
end newSlide

on addMetricCard(theSlide, labelText, valueText, posX, posY, w, accentColor, fillColor)
	my addBox(theSlide, posX, posY, w, 86, fillColor, fillColor, 0)
	my addBox(theSlide, posX + w - 7, posY, 7, 86, accentColor, accentColor, 0)
	my addText(theSlide, valueText, posX + 16, posY + 11, w - 35, 38, 30, accentColor, true, "left", false)
	my addText(theSlide, labelText, posX + 16, posY + 52, w - 35, 22, 13, ink2, false, "left", false)
end addMetricCard

tell application "Microsoft PowerPoint"
	activate
	set p to make new presentation
	delay 1

	-- Slide 1
	set s to make new slide at end of p
	set layout of s to slide layout blank
	set follow master background of s to false
	solid (fill format of background of s)
	set fore color of fill format of background of s to navy
	my addBox(s, 950, 0, 10, 540, orange, orange, 0)
	my addText(s, "DiffIntent-RTL", 410, 84, 475, 82, 48, pptWhite, true, "right", false)
	my addText(s, "זיהוי מטרת שינוי וחוסרים פונקציונליים בקוד", 410, 172, 475, 76, 30, {221, 231, 243}, true, "right", true)
	my addText(s, "RTL", 720, 248, 165, 42, 29, orange, true, "right", false)
	my addLine(s, 65, 314, 885, 314, {64, 91, 119}, 1.5, false)
	my addText(s, "קורן הנס ונועה סבג", 410, 341, 475, 36, 20, pptWhite, false, "right", true)
	my addText(s, "Deep Learning Project", 65, 342, 350, 34, 17, {170, 193, 219}, false, "left", false)
	my addText(s, "15 min", 65, 447, 130, 28, 14, orange, true, "left", false)
	my addText(s, "Final Presentation", 65, 478, 260, 24, 12, {170, 193, 219}, false, "left", false)
	my addNotes(s, "00:30\nמטרת השקופית: להציג את שאלת המחקר ואת מבנה ההרצאה.\n\nDiffIntent-RTL\n\nהפרויקט בוחן האם מודל יכול ללמוד מתוך שינוי קוד עצמו, ולא רק מתוך תמונת הקובץ לאחר השינוי. הקלט הוא שינוי אמיתי בקובץ חומרה, והפלט כולל שתי תחזיות משלימות. התחזית הראשונה מתארת את מטרת השינוי. התחזית השנייה מעריכה האם השינוי נראה שלם או שחסר בו רכיב פונקציונלי.\n\nהמיקוד הוא בקוד חומרה סינתזבילי, שבו שורה קצרה יכולה להשפיע על reset, על מכונת מצבים או על אות בקרה. לכן ההקשר המבני של השינוי חשוב במיוחד.\n\nבמהלך ההרצאה אציג את בניית מערך הנתונים, את ארבע משפחות המודלים, את תוצאות שתי המשימות ואת המגבלות שמגדירות מה ניתן להסיק.\n\nמשפט מעבר: נתחיל מדוגמה קטנה שממחישה מדוע שינוי שעובר בדיקה תחבירית עדיין עלול להיות חסר.\n\nמקורות: הצעת הפרויקט. סעיפים 1 ו-2 בדוח הסופי.")

	-- Slide 2
	set s to my newSlide(p, "חוסר גדול מסתתר בשינוי קטן", "02 / 14")
	my addBox(s, 48, 105, 505, 330, navy, navy, 0)
	my addCode(s, "@@ always_ff @(posedge clk_i) @@\n- if (!rst_ni) state_q <= IDLE;\n+ if (!rst_ni) state_q <= IDLE;\n+ else if (req_i) begin\n+   state_q <= BUSY;\n+   valid_o <= 1'b1;\n+ end", 72, 132, 455, 225, 18, {221, 231, 243})
	my addBox(s, 72, 374, 455, 36, {35, 54, 74}, {35, 54, 74}, 0)
	my addText(s, "What if the final assignment is missing?", 85, 379, 430, 24, 15, orange, true, "left", false)
	my addText(s, "השינוי עדיין יכול להיות תקין תחבירית", 585, 128, 320, 46, 24, navy, true, "right", true)
	my addText(s, "אבל ההתנהגות הרצויה אינה שלמה", 585, 183, 320, 44, 23, redColor, true, "right", true)
	my addLine(s, 580, 250, 905, 250, grayLine, 1, false)
	my addText(s, "מפתח אנושי קורא הקשר, מבנה והבדלים בין שורות. המודל חייב לקבל את אותם רמזים.", 585, 273, 320, 113, 20, ink2, false, "right", true)
	set mixedCodeReview to "מפתח אנושי בתהליך " & lri & "Code Review" & pdi & " קורא יחד את ההקשר, המבנה וההבדל בין השורות."
	my addText(s, mixedCodeReview, 585, 391, 320, 82, 18, blue, true, "right", true)
	my addNotes(s, "01:05\nמטרת השקופית: להמחיש את ההבדל בין תקינות תחבירית לבין שלמות פונקציונלית.\n\nבדוגמה מופיע שינוי קטן בבלוק שעוני. נוספה תגובה לבקשה ונוסף עדכון של אות תקפות. אם אחת משורות ההשמה חסרה, הקוד עדיין עשוי לעבור parser ואף לעבור קומפילציה, אבל ההתנהגות הרצויה כבר אינה שלמה. זו בדיוק הבעיה שמנגנוני בדיקה תחביריים אינם פותרים.\n\nCode Review\n\nמפתח אנושי אינו קורא רק את המילים בשורה. הוא משווה בין השורות שנוספו ונמחקו, בודק את ההקשר הסמוך ומזהה תבניות חומרה מוכרות כמו reset, guard ומעבר מצב. לכן מודל שימושי צריך לקבל גם את תוכן השורות וגם את תפקידן בתוך השינוי.\n\nחשוב להדגיש שהמערכת אינה מחליפה אימות פורמלי או סימולציה. מטרתה היא להוסיף אות הסתברותי שמכוון את תשומת הלב של הסוקר לשינויים חשודים.\n\nמשפט מעבר: מהדוגמה הזו נגזרות שתי משימות למידה שונות על אותו אובייקט קלט.\n\nמקורות: סעיפים 1 ו-3.3 בדוח הסופי.")

	-- Slide 3
	set s to my newSlide(p, "שתי שאלות מחקר, אובייקט למידה אחד", "03 / 14")
	my addBox(s, 500, 118, 405, 206, paleBlue, paleBlue, 0)
	my addText(s, "Intent", 535, 137, 335, 50, 30, blue, true, "right", false)
	my addText(s, "איזו מטרה עומדת מאחורי השינוי?", 535, 199, 335, 48, 22, navy, true, "right", true)
	my addText(s, "4 classes", 710, 267, 160, 26, 15, ink2, false, "right", false)
	my addBox(s, 55, 118, 405, 206, paleOrange, paleOrange, 0)
	my addText(s, "Completeness", 90, 137, 335, 50, 30, orange, true, "right", false)
	my addText(s, "האם השינוי נראה שלם?", 90, 199, 335, 48, 22, navy, true, "right", true)
	my addText(s, "binary task", 265, 267, 160, 26, 15, ink2, false, "right", false)
	my addLine(s, 480, 132, 480, 310, grayLine, 2, false)
	my addText(s, "ההשערה", 775, 354, 130, 30, 17, blue, true, "right", true)
	my addText(s, "ייצוג היררכי שמבחין בין שורות שנוספו, נמחקו ונשמרו ישפר את זיהוי החוסר.", 258, 387, 647, 58, 21, navy, true, "right", true)
	my addText(s, "CC2Vec   PatchNet   DeepJIT   CodeReviewer", 55, 458, 850, 30, 14, ink2, false, "center", false)
	my addNotes(s, "00:55\nמטרת השקופית: להגדיר במדויק את שתי שאלות המחקר.\n\nIntent\n\nהמשימה הראשונה היא סיווג מטרת השינוי לאחת מארבע מחלקות: תיקון תקלה, שינוי תכונה או התנהגות, ארגון מחדש וניקוי, או שינוי תצורה ותזמון. התוויות נבנו באופן חלש מהודעות השינוי, ולכן בהמשך נבחן האם הן באמת מודדות הבנת קוד.\n\nCompleteness\n\nהמשימה השנייה היא בינארית. המודל מבחין בין שינוי מקורי שנחשב שלם לבין גרסה זוגית שבה יצרנו חוסר מבוקר.\n\nשתי המשימות משתמשות באותו ייצוג פנימי. ההשערה המרכזית היא שמבנה היררכי שמבחין בין שורות שנוספו, נמחקו ונשמרו יסייע בעיקר בזיהוי חוסר. המחקרים הקודמים סיפקו את הבסיס לייצוג שינוי כאובייקט למידה ולשימוש במבנה קובץ, שורה ואסימון.\n\nמשפט מעבר: כדי לבדוק את ההשערה נדרש צינור שממיר היסטוריית קוד לניסוי מבוקר.\n\nמקורות: CC2Vec. PatchNet. DeepJIT. CodeReviewer. סעיפים 1 ו-2 בדוח.")

	-- Slide 4
	set s to my newSlide(p, "מהיסטוריית קוד לניסוי מבוקר", "04 / 14")
	set px to {740, 565, 390, 215, 40}
	set labels to {"OpenTitan Git History", "Diff Mining", "Weak Labels + Synthetic Holes", "Chronological Split", "Training & Evaluation"}
	repeat with i from 1 to 5
		set posX to item i of px
		my addBox(s, posX, 154, 145, 134, pptWhite, grayLine, 1.2)
		my addText(s, item i of labels, posX + 10, 178, 125, 76, 17, navy, true, "center", false)
		if i < 5 then my addLine(s, posX - 18, 221, posX - 30, 221, blue, 2.5, true)
	end repeat
	my addText(s, "5,903", 758, 314, 110, 34, 25, blue, true, "center", false)
	my addText(s, "2,843", 408, 314, 110, 34, 25, orange, true, "center", false)
	my addText(s, "5,500", 231, 314, 110, 34, 25, pGreen, true, "center", false)
	my addText(s, "raw candidates", 742, 349, 142, 24, 12, ink2, false, "center", false)
	my addText(s, "real examples", 392, 349, 142, 24, 12, ink2, false, "center", false)
	my addText(s, "total examples", 215, 349, 142, 24, 12, ink2, false, "center", false)
	my addBox(s, 55, 408, 850, 61, paleBlue, paleBlue, 0)
	my addText(s, "כל שינוי נשמר ברמת קובץ, והזוג המקורי והסינתטי נשאר באותה חלוקה.", 83, 420, 794, 38, 19, navy, true, "right", true)
	my addNotes(s, "01:15\nמטרת השקופית: להסביר את שרשרת הנתונים ואת מנגנוני ההגנה מפני דליפה.\n\nOpenTitan\n\nהכרייה מתחילה מהיסטוריית המאגר ומקבלת רק שינויים בקבצי חומרה תחת נתיבי RTL. קבצי בדיקות, קוד צד שלישי, תוצרים שנוצרו אוטומטית ושינויים גדולים מדי מסוננים. כל דוגמה מייצגת שינוי בקובץ אחד.\n\nWeak Labels\n\nמילות מפתח בהודעת השינוי משייכות את הדוגמה למחלקת מטרה. דוגמאות ללא התאמה או עם התאמה חזקה לכמה קבוצות מושלכות. זה מאפשר קנה מידה גדול, אך יוצר תלות בין מקור התווית לבין הטקסט שממנו היא נגזרה.\n\nSynthetic Holes\n\nלכל דוגמה אמיתית מנסים ליצור עותק חסר באמצעות שינוי מבוקר בתוך אזור השינוי בלבד.\n\nChronological Split\n\nהחלוקה נעשית לפי זמן. הזוג המקורי והמוטנטי נשאר תמיד באותה קבוצה. אוצר המילים נבנה מקבוצת האימון בלבד. כך נשמרת הפרדה בין אימון, אימות ובדיקה.\n\nמשפט מעבר: כעת נבחן כמה דוגמאות שרדו כל שלב ומהי התפלגות המחלקות.\n\nמקורות: סעיפים 3.1 עד 3.5 בדוח הסופי.")

	-- Slide 5
	set s to my newSlide(p, "מערך הנתונים: כרונולוגי, מאוזן בזוגות", "05 / 14")
	my addPicture(s, "figure_dataset_overview.png", 48, 108, 390, 349)
	my addMetricCard(s, "raw candidates", "5,903", 493, 114, 412, blue, paleBlue)
	my addMetricCard(s, "weak-labeled real", "2,843", 493, 213, 412, orange, paleOrange)
	my addMetricCard(s, "after synthetic holes", "5,500", 493, 312, 412, pGreen, paleGreen)
	my addText(s, "train 3,873    validation 830    test 797", 493, 422, 412, 37, 16, navy, true, "center", false)
	my addNotes(s, "01:05\nמטרת השקופית: לכמת את מערך הנתונים ולהראות היכן נוצרת הטיה.\n\nהכרייה הפיקה 5,903 מועמדים גולמיים. לאחר הסרת דוגמאות ללא התאמת מילות מפתח ולאחר הסרת מקרים עמומים נשארו 2,843 דוגמאות אמיתיות מתויגות. מתוכן נוצרו 2,657 גרסאות חסרות, ולכן מערך הנתונים הסופי כולל 5,500 דוגמאות. לא מכל דוגמה אפשר ליצור חוסר תקף לפי כללי המוטציה.\n\nהחלוקה הכרונולוגית היא 3,873 דוגמאות לאימון, 830 לאימות ו-797 לבדיקה. משימת החוסר כמעט מאוזנת: 51.7 אחוז דוגמאות שלמות ו-48.3 אחוז דוגמאות חסרות. לעומת זאת, משימת המטרה אינה מאוזנת. המחלקה הקטנה ביותר מהווה רק 8.5 אחוז מהנתונים, ולכן המדד המרכזי הוא ממוצע שווה בין המחלקות ולא דיוק בלבד.\n\nMacro-F1\n\nהמדד נותן לכל מחלקה משקל שווה, ולכן הוא חושף כשל במחלקה נדירה גם כאשר הדיוק הכולל נראה סביר.\n\nמשפט מעבר: השאלה הבאה היא כיצד נוצרה דוגמה חסרה ומה בדיוק היא מייצגת.\n\nמקורות: סעיף 3.4 בדוח. outputs/metrics/dataset_stats.json. figure_dataset_overview.png.")

	-- Slide 6
	set s to my newSlide(p, "יצירת חוסרים סינתטיים בתוך אזור השינוי", "06 / 14")
	my addBox(s, 505, 118, 400, 255, navy, navy, 0)
	my addText(s, "COMPLETE", 535, 132, 140, 27, 14, pGreen, true, "left", false)
	my addCode(s, "+ if (req_i) begin\n+   state_d = BUSY;\n+   valid_d = 1'b1;\n+ end", 535, 171, 335, 150, 19, {221, 231, 243})
	my addBox(s, 55, 118, 400, 255, {38, 47, 62}, {38, 47, 62}, 0)
	my addText(s, "SYNTHETIC HOLE", 85, 132, 210, 27, 14, orange, true, "left", false)
	my addCode(s, "+ if (req_i) begin\n+   state_d = BUSY;\n\n+ end", 85, 171, 335, 150, 19, {221, 231, 243})
	my addLine(s, 495, 245, 465, 245, orange, 3, true)
	my addText(s, "drop_added_line", 337, 389, 285, 30, 18, orange, true, "center", false)
	my addText(s, "82.2%", 352, 425, 255, 43, 31, redColor, true, "center", false)
	my addText(s, "of test synthetic examples", 341, 470, 278, 22, 12, ink2, false, "center", false)
	my addNotes(s, "01:10\nמטרת השקופית: להסביר את יצירת התווית למשימת החוסר ואת מגבלותיה.\n\nהדוגמה המקורית נשמרת ללא שינוי ומקבלת תווית שלמה. לאחר מכן נוצר עותק שבו מסירים או משנים רכיב בתוך האזור שהשתנה. בדוגמה על המסך הוסרה שורת השמה שנוספה, ולכן המבנה הכללי נשמר אך ההתנהגות חלקית.\n\ndrop_added_line\n\nזו המוטציה הדומיננטית. היא מייצגת 304 מתוך 370 דוגמאות החוסר בקבוצת הבדיקה, כלומר 82.2 אחוז. קיימות גם הסרת תנאי או assertion, הסרת השמת reset, החלפת קבוע בינארי ושינוי אופרטורים. חלק מהמשפחות נדירות מאוד או אינן מופיעות כלל בבדיקה.\n\nהיתרון המתודולוגי הוא שליטה מלאה בתווית והשוואה זוגית בין שינוי מקורי לגרסה חסרה. החיסרון הוא שהדוגמאות הסינתטיות אינן מכסות את מלוא המורכבות של טעויות אנוש אמיתיות. לכן התוצאה מודדת זיהוי של משפחות חוסר מוגדרות, ולא שלמות פונקציונלית כללית.\n\nמשפט מעבר: על אותו מערך נתונים נשווה כעת בין קו בסיס לקסיקלי לשלושה מודלים עצביים.\n\nמקורות: סעיף 3.3. סעיפים 7.4 ו-8 בדוח.")

	-- Slide 7
	set s to my newSlide(p, "השוואת ארבע משפחות מודלים", "07 / 14")
	set cardX to {715, 495, 275, 55}
	set cardTitles to {"TF-IDF + Logistic Regression", "MLP", "BiGRU", "Hierarchical Transformer"}
	set cardSubs to {"sparse lexical features", "pooled token embeddings", "flat sequence encoder", "line encoder + diff structure"}
	set cardColors to {paleBlue, paleGreen, paleOrange, paleRed}
	set accentColors to {blue, pGreen, orange, redColor}
	repeat with i from 1 to 4
		set posX to item i of cardX
		my addBox(s, posX, 120, 190, 238, item i of cardColors, item i of cardColors, 0)
		my addText(s, (i as text), posX + 18, 137, 38, 36, 25, item i of accentColors, true, "left", false)
		my addText(s, item i of cardTitles, posX + 18, 184, 154, 65, 18, navy, true, "left", false)
		my addText(s, item i of cardSubs, posX + 18, 263, 154, 53, 13, ink2, false, "left", false)
	end repeat
	my addBox(s, 55, 388, 850, 81, paleBlue, paleBlue, 0)
	set mixedMultiTask to "אותו ייצוג משמש לשתי המשימות באמצעות " & lri & "Multi-task head" & pdi & " וכל משימה מקבלת פלט נפרד."
	my addText(s, mixedMultiTask, 78, 397, 797, 58, 19, navy, true, "right", true)
	my addNotes(s, "01:05\nמטרת השקופית: להציג את סולם המורכבות ואת עקרון ההשוואה ההוגנת.\n\nTF-IDF + Logistic Regression\n\nקו הבסיס משתמש בצירופי מילים ובצירופי תווים. הוא אינו לומד סדר היררכי, אבל מסוגל לזהות רמזים לקסיקליים חזקים כמו שמות אותות, מילות מפתח ואופרטורים.\n\nMLP\n\nהמודל מחשב ממוצע של ייצוגי האסימונים ומעביר אותו דרך שתי שכבות מלאות. סדר האסימונים כמעט ואינו נשמר.\n\nBiGRU\n\nהמודל קורא רצף שטוח של אסימונים בשני הכיוונים ומשתמש במנגנון attention לצורך איגום. הוא שומר סדר, אך אינו מפריד במפורש בין שורות.\n\nHierarchical Transformer\n\nהמודל מקודד תחילה כל שורה ולאחר מכן את רצף השורות. הוא מקבל גם מידע על סוג השורה.\n\nבמודלים העצביים ייצוג משותף מזין שני ראשי פלט. האימון משתמש ב-cross-entropy וב-AdamW. הריצות העיקריות חזרו בשלושה seeds. תקציב האימון היה שישה epochs עם early stopping קצר, ולכן יש להביא בחשבון אפשרות של אימון חסר.\n\nמשפט מעבר: נפתח את המודל ההיררכי ונראה היכן נכנס מידע המבנה.\n\nמקורות: סעיפים 4.1 עד 4.3 וסעיף 5 בדוח.")

	-- Slide 8
	set s to my newSlide(p, "הארכיטקטורה ההיררכית", "08 / 14")
	set ax to {735, 565, 395, 225, 55}
	set al to {"Typed Diff Lines", "Token Embedding + BiGRU", "Line Vector", "Transformer Encoder", "Intent Head\nHole Head"}
	set ac to {paleBlue, paleGreen, paleOrange, paleBlue, paleRed}
	repeat with i from 1 to 5
		set posX to item i of ax
		my addBox(s, posX, 154, 150, 132, item i of ac, item i of ac, 0)
		my addText(s, item i of al, posX + 12, 177, 126, 79, 17, navy, true, "center", false)
		if i < 5 then my addLine(s, posX - 3, 220, posX - 17, 220, blue, 2.5, true)
	end repeat
	my addText(s, "ADD   DEL   CONTEXT", 741, 306, 138, 25, 13, blue, true, "center", false)
	my addBox(s, 55, 368, 850, 91, paleOrange, paleOrange, 0)
	set mixedLineType to "הייצוג " & lri & "line-type embedding" & pdi & " מוסיף מידע מפורש על תפקיד כל שורה בתוך השינוי."
	my addText(s, mixedLineType, 78, 383, 797, 57, 20, navy, true, "right", true)
	my addNotes(s, "01:20\nמטרת השקופית: להסביר את הארכיטקטורה ואת ההטיה המבנית שהיא מכניסה.\n\nTyped Diff Lines\n\nכל שורה מקבלת סוג מפורש. הסוגים כוללים שורה שנוספה, שורה שנמחקה, שורת הקשר, כותרת מקטע, נתיב קובץ וריפוד. אותו רצף אסימונים עשוי לקבל משמעות שונה לפי סוג השורה.\n\nToken Embedding + BiGRU\n\nבתוך כל שורה, ייצוגי אסימונים ומיקומים עוברים במקודד דו-כיווני. התוצאה היא וקטור אחד לכל שורה.\n\nTransformer Encoder\n\nוקטורי השורות עוברים בשתי שכבות עם ארבעה ראשי attention. כך המודל יכול לקשר בין reset שנמחק במקום אחד לבין השמה שנוספה במקום אחר. לאחר איגום מתקבל ייצוג יחיד של כל השינוי.\n\nIntent Head\nHole Head\n\nכל ראש מפיק תחזית נפרדת, אך שניהם משתמשים בייצוג המשותף. הקלט מוגבל ל-128 שורות ול-64 אסימונים בשורה. בעת קיטום נשמרות קודם השורות שנוספו ונמחקו ולאחר מכן ההקשר הקרוב.\n\nהניסוי הסיבתי המרכזי מסיר רק את ייצוג סוג השורה ומשאיר את שאר הארכיטקטורה קבועה.\n\nמשפט מעבר: נבחן תחילה את משימת המטרה, שבה דווקא קו הבסיס הפשוט מוביל.\n\nמקורות: סעיפים 3.5, 4.3 ו-4.4 בדוח.")

	-- Slide 9
	set s to my newSlide(p, "סיווג המטרה: המודל הפשוט ניצח", "09 / 14")
	my addPicture(s, "figure_intent_per_class_f1.png", 48, 128, 570, 334)
	my addMetricCard(s, "test Macro-F1", "0.4197", 657, 137, 248, blue, paleBlue)
	set mixedTfidf to "קו הבסיס " & lri & "TF-IDF" & pdi & " השיג את התוצאה הטובה ביותר. האות הלקסיקלי הספיק כדי לעקוף את המודלים העמוקים."
	my addText(s, mixedTfidf, 657, 230, 248, 172, 20, ink2, false, "right", true)
	my addBox(s, 657, 415, 248, 47, paleOrange, paleOrange, 0)
	my addText(s, "refactor_cleanup", 674, 425, 215, 26, 14, orange, true, "left", false)
	my addNotes(s, "01:10\nמטרת השקופית: להציג את התוצאה השלילית החשובה במשימת המטרה.\n\nTF-IDF\nMacro-F1 = 0.4197\n\nזהו הערך הגבוה ביותר בניסוי העיקרי. שלושת המודלים העצביים נמצאים סביב 0.296 עד 0.302. התוצאה מראה שבמערך הנתונים הנוכחי רמזים לקסיקליים מספיקים כדי לעקוף ייצוגים עמוקים יותר.\n\nהיתרון אינו אחיד בין המחלקות. בריצת הייחוס, המחלקה של שינוי תכונה או התנהגות מגיעה ל-F1 של 0.6387, בעוד המחלקה הנדירה של ארגון מחדש וניקוי מגיעה ל-0.1642 בלבד. במודל ההיררכי אותה מחלקה קורסת ל-0.0. היא גם נדירה וגם חופפת סמנטית לתיקוני תקלה ולשינויי התנהגות.\n\nיש שתי הסתייגויות. ראשית, התוויות נגזרו ממילים בהודעות השינוי ולכן צפוי אות לקסיקלי חזק. שנית, תקציב האימון העצבּי היה קצר, ולכן חלק מהפער עשוי לנבוע מאימון חסר. למרות זאת, הפער העקבי מחייב בדיקת בקרה.\n\nמשפט מעבר: נבדוק מה קורה כאשר המודל מקבל רק את המקור שממנו נוצרה התווית.\n\nמקורות: סעיפים 6.1, 6.3 ו-7.1 בדוח. figure_intent_per_class_f1.png.")

	-- Slide 10
	set s to my newSlide(p, "בדיקת בקרה חושפת דליפה", "10 / 14")
	set bx to {610, 340, 70}
	set bt to {"commit message", "weak label", "message-only model"}
	repeat with i from 1 to 3
		set posX to item i of bx
		my addBox(s, posX, 155, 230, 94, paleBlue, paleBlue, 0)
		my addText(s, item i of bt, posX + 18, 181, 194, 42, 20, navy, true, "center", false)
		if i < 3 then my addLine(s, posX - 10, 202, posX - 30, 202, redColor, 3, true)
	end repeat
	my addText(s, "0.9855", 337, 290, 290, 71, 48, redColor, true, "center", false)
	my addText(s, "Macro-F1", 398, 358, 168, 28, 17, ink2, true, "center", false)
	my addBox(s, 70, 417, 770, 59, paleRed, paleRed, 0)
	my addText(s, "המדד כמעט משחזר את מנגנון התיוג, ולכן אינו הוכחה להבנת קוד טהורה.", 95, 427, 720, 39, 20, navy, true, "right", true)
	my addNotes(s, "01:05\nמטרת השקופית: לבדוק את תקפות משימת המטרה ולא רק את ביצועי המודל.\n\nהתיוג החלש נוצר באמצעות התאמה בין מילות מפתח לבין הודעת השינוי. לכן אימנו בדיקת בקרה שמקבלת רק את אותה הודעה ואינה רואה את קוד החומרה.\n\nMessage-only TF-IDF\nMacro-F1 = 0.9855\n\nהתוצאה כמעט מושלמת. המשמעות אינה שהמודל מבין היטב את השינוי, אלא שהוא משחזר את הכלל שיצר את התווית. זהו מקרה של דליפת יעד ברמת הגדרת המשימה. הבדיקה עדיין שימושית למחקר בקנה מידה גדול, אך היא אינה יכולה לשמש הוכחה להבנת קוד טהורה.\n\nהפתרון למחקר המשך הוא מקור תוויות עצמאי. אפשר לבנות מדגם מתויג ידנית, להשתמש בנתוני review או issue, או לבצע הסכמה בין כמה מעריכים. חשוב שהמידע שמגדיר את התווית לא יהיה אותו מידע שהמודל מקבל כקלט בבדיקת הבקרה.\n\nמשפט מעבר: משימת החוסר אינה משתמשת בהודעת השינוי ליצירת התווית, ולכן שם אפשר לבחון באופן נקי יותר את תרומת המבנה.\n\nמקורות: סעיפים 6.2, 7.1 ו-8 בדוח.")

	-- Slide 11
	set s to my newSlide(p, "זיהוי חוסר: המבנה ההיררכי ניצח", "11 / 14")
	my addMetricCard(s, "hole F1", "0.6029", 645, 104, 260, pGreen, paleGreen)
	my addMetricCard(s, "AUROC", "0.7352", 350, 104, 260, blue, paleBlue)
	my addMetricCard(s, "false positives", "172 → 81", 55, 104, 260, orange, paleOrange)
	my addPicture(s, "figure_hole_confusion_panels.png", 94, 214, 772, 289)
	my addNotes(s, "01:20\nמטרת השקופית: להציג את התוצאה החיובית המרכזית של הפרויקט ולהסביר את מקור השיפור.\n\nHierarchical Transformer\nHole F1 = 0.6029\nAUROC = 0.7352\n\nאלה הממוצעים על פני שלושה seeds, והם הגבוהים ביותר במשימת החוסר. המדד F1 מאזן בין precision לבין recall עבור מחלקת החוסר. המדד AUROC בוחן את יכולת הדירוג של המודל על פני כל ספי ההחלטה ולא רק בסף אחד.\n\nמטריצות הבלבול מציגות ריצת ייחוס. קו הבסיס מסווג נכון 202 דוגמאות חסרות, והמודל ההיררכי מסווג נכון 203. מספר החוסרים שהתגלו כמעט זהה. ההבדל הגדול הוא בדוגמאות השלמות: מספר התראות השווא יורד מ-172 ל-81.\n\nTF-IDF\n[[255, 172], [168, 202]]\n\nHierarchical Transformer\n[[346, 81], [167, 203]]\n\nלשימוש ב-Code Review זו תוצאה חשובה. כלי שמתריע יותר מדי נשחק במהירות. הפחתת התראות שווא תוך שמירה על recall דומה הופכת את המודל לשמרני ושימושי יותר.\n\nמשפט מעבר: כדי לבדוק אם השיפור נובע באמת מסוג השורה, נסיר רק את הרכיב הזה.\n\nמקורות: סעיפים 6.1, 7.2 ו-7.6 בדוח. figure_hole_confusion_panels.png.")

	-- Slide 12
	set s to my newSlide(p, "מידע על סוג השורה הוא רכיב מהותי", "12 / 14")
	my addMetricCard(s, "Δ hole F1", "−0.1305", 140, 103, 290, redColor, paleRed)
	my addMetricCard(s, "Δ AUROC", "−0.1058", 530, 103, 290, redColor, paleRed)
	my addPicture(s, "figure_ablation_results.png", 49, 205, 862, 297)
	my addNotes(s, "01:10\nמטרת השקופית: לבודד את התרומה של מידע סוג השורה.\n\nNo Line-Type Embeddings\n\nבניסוי הזה נשמרים מקודד האסימונים, המקודד ההיררכי, מספר השכבות, תקציב האימון והחלוקה. הרכיב היחיד שמוסר הוא הייצוג שמציין אם השורה נוספה, נמחקה או משמשת כהקשר.\n\nDelta Hole F1 = -0.1305\nDelta AUROC = -0.1058\n\nבממוצע של שלושה seeds, המדד F1 יורד מ-0.6029 ל-0.4724 והמדד AUROC יורד מ-0.7352 ל-0.6294. בריצת הייחוס השורה הראשונה במטריצת הבלבול נשארת זהה, אבל המודל מאבד 66 זיהויים נכונים של חוסרים. כלומר המידע המבני מסייע בעיקר לזהות שהשינוי החסר אכן חשוד, ולא רק לדחות דוגמאות שלמות.\n\nזו הראיה הסיבתית החזקה ביותר בפרויקט. השיפור אינו נובע רק ממספר פרמטרים גדול יותר. הוא קשור להטיה מבנית שמתאימה לאופי של שינוי קוד. ניסויי הסרת הקשר והפרדת המשימות מספקים תמונה נוספת, אך הם בוצעו על seed יחיד ולכן המסקנה מהם חלשה יותר.\n\nמשפט מעבר: גם תוצאה חזקה זו חייבת להיקרא בתוך גבולות מערך הנתונים.\n\nמקורות: סעיפים 6.2 ו-7.3 בדוח. figure_ablation_results.png.")

	-- Slide 13
	set s to my newSlide(p, "מה המודל עדיין לא הוכיח", "13 / 14")
	my addText(s, "82.2%", 660, 108, 245, 68, 44, redColor, true, "right", false)
	my addText(s, "drop_added_line", 660, 177, 245, 28, 17, navy, true, "right", false)
	my addBox(s, 660, 221, 245, 24, paleRed, paleRed, 0)
	my addBox(s, 704, 221, 201, 24, redColor, redColor, 0)
	my addText(s, "mutation distribution", 660, 253, 245, 24, 12, ink2, false, "right", false)
	set ly to {106, 230, 354}
	set lt to {"Synthetic Coverage", "Rare Mutations", "External Validity"}
	set lh to {"רוב הדוגמאות נוצרו מהסרת שורה שנוספה.", "יש מעט דוגמאות לשינויים סמנטיים עדינים.", "לא בוצעה הערכה סופית על פרויקט חיצוני."}
	repeat with i from 1 to 3
		set posY to item i of ly
		if i is 1 then
			my addBox(s, 55, posY, 560, 99, paleBlue, paleBlue, 0)
		else if i is 2 then
			my addBox(s, 55, posY, 560, 99, paleOrange, paleOrange, 0)
		else
			my addBox(s, 55, posY, 560, 99, paleGreen, paleGreen, 0)
		end if
		my addText(s, item i of lt, 280, posY + 8, 305, 26, 16, blue, true, "right", false)
		my addText(s, item i of lh, 76, posY + 38, 509, 45, 18, navy, false, "right", true)
	end repeat
	my addText(s, "נדרש סט בדיקה ידני של חוסרים אמיתיים.", 660, 330, 245, 70, 22, navy, true, "right", true)
	my addNotes(s, "01:05\nמטרת השקופית: להגדיר במפורש את גבול התוקף של המסקנות.\n\nהמגבלה הראשונה היא כיסוי סינתטי. 82.2 אחוז מדוגמאות החוסר בבדיקה נוצרו מהסרת שורה שנוספה. לכן המדד הכולל מושפע בעיקר ממשפחה שקל יחסית לזהות. recall עבור הסרת guard או assertion הוא רק 0.2931. עבור החלפת קבוע בינארי הוא 0.0, אך קיימות רק שש דוגמאות.\n\nהמגבלה השנייה היא תמיכה נמוכה. בבדיקה יש שתי דוגמאות בלבד להסרת השמת reset או default, ואין כלל דוגמאות לכמה משפחות של החלפת אופרטורים והסרת מקטע. אי אפשר להסיק מהן יכולת הכללה.\n\nהמגבלה השלישית היא תוקף חיצוני. המחקר על Caliptra בוצע בקנה מידה קטן ובפרוטוקול שונה. הוא מראה שינוי בהתפלגות ובכיסוי התיוג, אך אינו שקול לניסוי המלא על OpenTitan.\n\nניתוח איכותני מצא גם התראות שווא בטוחות בשינויי clock ו-reset, והחמצות בטוחות בהסרת assertion או בשינויי parameter. לכן נדרש מערך בדיקה ידני של חוסרים אמיתיים לפני שימוש מעשי.\n\nמשפט מעבר: לאחר ההסתייגויות אפשר לסכם שלוש מסקנות שמגובות ישירות בניסוי.\n\nמקורות: סעיפים 7.4, 7.5, 7.7 ו-8 בדוח.")

	-- Slide 14
	set s to my newSlide(p, "מסקנות ושאלות", "14 / 14")
	my addMetricCard(s, "Intent Macro-F1", "0.4197", 55, 112, 250, blue, paleBlue)
	my addMetricCard(s, "hole F1", "0.6029", 55, 214, 250, pGreen, paleGreen)
	my addMetricCard(s, "hole AUROC", "0.7352", 55, 316, 250, orange, paleOrange)
	my addText(s, "1", 836, 113, 50, 50, 30, blue, true, "center", false)
	my addText(s, "ייצוג מבנה השינוי חשוב יותר מנפח המודל.", 370, 112, 446, 54, 22, navy, true, "right", true)
	my addText(s, "2", 836, 211, 50, 50, 30, pGreen, true, "center", false)
	my addText(s, "מידע מפורש על סוג השורה מצמצם התראות שווא ומשפר זיהוי חוסר.", 370, 210, 446, 64, 21, navy, true, "right", true)
	my addText(s, "3", 836, 309, 50, 50, 30, orange, true, "center", false)
	set mixedCommitMessage to "מקור התוויות חייב להיות עצמאי. אין להעריך הבנת קוד לפי " & lri & "commit message" & pdi
	my addText(s, mixedCommitMessage, 370, 301, 446, 85, 20, redColor, true, "right", true)
	my addLine(s, 55, 445, 905, 445, grayLine, 1, false)
	my addText(s, "github.com/korrenhannes/diffintent-rtl", 55, 463, 460, 28, 14, blue, false, "left", false)
	my addText(s, "שאלות?", 697, 454, 208, 44, 29, navy, true, "right", true)
	my addNotes(s, "00:45\nמטרת השקופית: לסיים בשלוש טענות מדויקות ולפתוח לשאלות.\n\nמסקנה ראשונה. במשימת המטרה, קו בסיס לקסיקלי פשוט השיג את התוצאה הטובה ביותר. זו אינה כישלון של המחקר, אלא עדות לכך שהתיוג והנתונים מכילים אות מילולי חזק ושמודלים עמוקים אינם עדיפים אוטומטית.\n\nמסקנה שנייה. במשימת החוסר, המבנה ההיררכי השיג את המדדים הטובים ביותר והפחית באופן משמעותי התראות שווא. ניסוי הסרת ייצוג סוג השורה תומך בטענה שמידע מפורש על תפקיד השורה הוא רכיב מהותי.\n\nמסקנה שלישית. מקור התוויות למשימת המטרה חייב להיות עצמאי. אין להעריך הבנת קוד באמצעות תווית שנגזרה מהודעת השינוי ואז להציג את שחזור ההודעה כהבנת קוד.\n\nהמשך העבודה הטבעי הוא מדגם מתויג ידנית, איזון טוב יותר בין משפחות חוסר, הרחבה לפרויקטים נוספים ושילוב מבנה חומרה עשיר יותר.\n\nמשפט סיום מוצע: הפרויקט מספק צינור מלא ושחזורי למחקר בשינויי RTL, יחד עם תוצאה חיובית על מבנה השינוי ותוצאה שלילית חשובה על תקפות התיוג.\n\nכעת אפשר לעבור לשאלות.\n\nמקור: סעיפים 6 עד 8 בדוח הסופי.")

	-- Backup 1
	set s to my newSlide(p, "גיבוי: מטריצות בלבול", "A1")
	my addPicture(s, "erroranalysis_confusion_full_tfidf_lr.png", 100, 126, 350, 292)
	my addPicture(s, "erroranalysis_confusion_full_hierarchical_transformer.png", 510, 126, 350, 292)
	my addNotes(s, "שקופית גיבוי. מומלץ לפתוח אותה רק אם נשאלת שאלה על דפוסי הטעות במשימת המטרה.\n\nכך קוראים את התרשימים: כל שורה מייצגת מחלקה אמיתית וכל עמודה מייצגת תחזית. ערך גבוה על האלכסון הוא סיווג נכון. ערכים מחוץ לאלכסון מראים בין אילו מחלקות המודל מתבלבל.\n\nTF-IDF\n\nקו הבסיס מזהה היטב יחסית שינויי תכונה או התנהגות, אך מתקשה במחלקת ארגון מחדש וניקוי. בריצת הייחוס רק 11 מתוך 102 דוגמאות במחלקה זו מסווגות נכון. חלק גדול מועבר לתיקון תקלה או לשינוי התנהגות.\n\nHierarchical Transformer\n\nהמודל ההיררכי קורס לחלוטין במחלקת ארגון מחדש וניקוי באותה ריצה. בנוסף, 92 מתוך 188 דוגמאות של תצורה ותזמון מסווגות כשינוי תכונה או התנהגות. דוגמאות כמו הוספת clock ו-reset אכן מכילות גם שינוי תפקודי, ולכן גבולות המחלקות עצמם אינם חדים.\n\nהמסר לשאלה: הבעיה אינה רק חוסר איזון. קיימת גם חפיפה סמנטית ורעש בתיוג החלש.\n\nמקורות: סעיף 7.1 בדוח. erroranalysis_confusion_full_tfidf_lr.png. erroranalysis_confusion_full_hierarchical_transformer.png.")

	-- Backup 2
	set s to my newSlide(p, "גיבוי: ביצועים לפי סוג שינוי", "A2")
	my addPicture(s, "figure_hole_mutation_recall.png", 140, 103, 680, 386)
	my addNotes(s, "שקופית גיבוי. מומלץ לפתוח אותה אם נשאלת שאלה על סוגי החוסרים שהמודל מזהה.\n\nהציר האופקי מפריד בין משפחות המוטציה, והציר האנכי מציג recall על דוגמאות חסרות בלבד. גודל המדגם מופיע מתחת לכל משפחה ולכן חשוב לא לפרש כל עמודה באותה רמת ביטחון.\n\nDrop Added Line\nSupport = 304\nRecall = 0.6086\n\nזו הקבוצה הגדולה ביותר ולכן היא שולטת במדד הכולל.\n\nRemove Guard or Assertion\nSupport = 58\nRecall = 0.2931\n\nהמודל מתקשה יותר כאשר החוסר סמנטי ועדיין משאיר שינוי שנראה סביר מבחינה לקסיקלית.\n\nFlip Binary Constant\nSupport = 6\nRecall = 0.0\n\nהמספר מדאיג אך המדגם קטן מדי למסקנה יציבה.\n\nRemove Reset or Default\nSupport = 2\nRecall = 0.5\n\nגם כאן אין בסיס סטטיסטי להכללה. אין דוגמאות בדיקה לכמה משפחות נוספות.\n\nהמסר לשאלה: המדד הכולל משקף בעיקר הסרת שורה, ולא יכולת כללית לזהות כל חוסר חומרה.\n\nמקורות: סעיף 7.4 בדוח. figure_hole_mutation_recall.png.")

	-- Backup 3
	set s to my newSlide(p, "גיבוי: מחקרי הרחבה", "A3")
	my addText(s, "Improved Weak Labeling", 48, 101, 264, 29, 16, blue, true, "center", false)
	my addPicture(s, "labeler_improvement.png", 48, 137, 264, 170)
	my addText(s, "Hardware-aware Features", 348, 101, 264, 29, 16, pGreen, true, "center", false)
	my addPicture(s, "rtl_features_cv.png", 360, 137, 240, 172)
	my addText(s, "Cross-project Study", 648, 101, 264, 29, 16, orange, true, "center", false)
	my addPicture(s, "generalization_compare.png", 648, 137, 264, 103)
	my addBox(s, 48, 347, 864, 112, paleBlue, paleBlue, 0)
	my addText(s, "Medium-scale studies", 71, 366, 230, 27, 18, redColor, true, "left", false)
	my addText(s, "המספרים אינם בני השוואה ישירה לניסוי המלא. הם מצביעים על שיפור כיסוי התיוג, ערך של מאפייני חומרה ופער בין פרויקטים.", 320, 359, 565, 73, 18, navy, false, "right", true)
	my addNotes(s, "שקופית גיבוי. מומלץ לפתוח אותה אם נשאלת שאלה על הכללה, שיפור התיוג או המשך עבודה.\n\nהסתייגות מרכזית: שלושת המחקרים בוצעו על מערך בינוני או בקנה מידה קטן, עם פרוטוקולים שונים מהניסוי המלא. אין להשוות את הערכים המוחלטים ישירות לטבלה הראשית.\n\nImproved Weak Labeling\n\nהרחבת מילון המילים הורידה את שיעור ההשלכה ב-OpenTitan מ-29 אחוז ל-16 אחוז, וב-Caliptra מ-53 אחוז ל-25 אחוז. הפער בין הפרויקטים הצטמצם, אך הודעות שמתארות מה השתנה ולא מדוע עדיין אינן פתירות באמצעות מילות מפתח בלבד.\n\nHardware-aware Features\n\nמודל Random Forest עם 18 מאפיינים פרשניים הגיע בחמש חלוקות ל-Macro-F1 של 0.525 בתוספת או הפחתה של 0.114. קו הבסיס הטקסטואלי באותו פרוטוקול הגיע ל-0.544 בתוספת או הפחתה של 0.053. המסקנה אינה שהמאפיינים מנצחים, אלא שהם מתקרבים לביצועי טקסט וחושפים אילו תכונות שינוי נושאות מידע.\n\nCross-project Study\n\nבמדגם הקטן, OpenTitan היה מוטה לשינויי תכונה ואילו Caliptra היה מוטה לתיקוני תקלה. השינוי בהתפלגות מסביר מדוע יש לצפות לירידה בהכללה בין פרויקטים.\n\nCode-review Assistant\n\nנבנתה שכבת יישום שמחזירה תחזית מטרה וציון חוסר. היא מדגימה שימוש אפשרי, אך אינה מהווה הערכת מוצר או אישור לפריסה.\n\nמקורות: סעיף 7.7 בדוח. labeler_improvement.png. rtl_features_cv.png. generalization_compare.png.")

	save p in outPath as save as Open XML presentation
	delay 5
	return count slides of p
end tell
