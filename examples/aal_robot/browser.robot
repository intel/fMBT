*** Settings ***
Documentation				This is a basic test
Library					SeleniumLibrary

*** Keywords ***
Open webpage
	[Arguments]			${url}	${browser}
	[Documentation]			As a user I can open the duckduckgo page
	log				${url}
	open browser			${url}	${browser}
	wait until page contains	DuckDuckGo

Make search
	[Arguments]			${text}		${search_button}	${search_text}
	[Documentation]			The user search ${search_text}
	input text			${text}	${search_text}
	click element			${search_button}
	wait until page contains	${search_text}

Close
	Close Browser
