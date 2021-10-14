templates/cow.js: cow.cs
	coffee -o templates cow.cs

dev :
	coffee -w -o templates cow.cs
