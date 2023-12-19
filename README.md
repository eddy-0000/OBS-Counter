# OBS-Counter

This script allows you to add a counter to your streams/recording in OBS.
It allows you to decrease/increase the counter via hotkey which are set in the hotkey settings in OBS.
Optionally a sound effect can also be assigned to the counter when it is increased.
 
## How to use

Simply add the counter.py file to your scripts and change your script settings accordingly.

![Script Settings](/Screenshots/Settings.png?raw=true)

The name of the counter can be changed in the <strong>"Counter Name"</strong> textfield.
Through the <strong>"Sound On?"</strong> toggle, one may select if the selected sound effect is played or not upon an increase in the counter.
Through the <strong>"Counter"</strong> slider one can manully adjust the current number, either by sliding the slider or entering a number.
In the <strong>"Text Source"</strong> and <strong>"Sound Source"</strong> their dedicated OBS sources are assigned.

![Script Settings](/Screenshots/OBS_Settings.png?raw=true)

Through the OBS settings, under the menu <strong>"Hotkeys"</strong> a hotkey for the increase and one for the decrease can be assigned. The Hotkeys are called <strong>"Counter Increase"</strong> and <strong>"Counter Decrease"</strong>.

## License

MIT