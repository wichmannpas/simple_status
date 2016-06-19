Simple Status
=============

This is a very simple status monitoring script which frequently checks the availability of a service. It is capable of sending a notification email if the service is unavailable and generates a static overview displaying the current status of all configured services and the average uptime statistics.

In order to check whether a service is available, it tries to fetch the configured url and searches for a defined pattern on the received data. If the pattern is not contained in the result or the connection fails, the service is marked as down and the configured email action is triggered.

This is a very primitive way of checking the availability, but it should be enough in most situations.

Installation
-----------

The script uses a file named *config* located in the same directory as the script itself to load the configuration value. You can use the file *config.example* from the repository as a template for your configuration.

Most important are the *hosts*. That configuration contains a list of hosts, where each host is a list containing the url to fetch and the pattern to search for on that page.

In order to get email alerts, you need to modify the *mail_command* configuration. If you do not want to get email alerts, leave the value as it is. Otherweise you need to specify a command which send you an email. An example would be ```echo "" | mail -s "{}" foobar@example```.
You can configure any command as *mail_command*; the only requirement is that the command can be executed successfully on the host where the script is running.

After you have created the configuration, you should run the script manually once in order to ensure that everything works as intended. Then you can configure a cronjob which triggers the script. The script does not require any specific frequency for it to be executed (it does not even need to be consistent). Depending on your needs this can be every minute, every 5 minutes or even every hour; email alerts may however arrive later and the downtime displayed in the statistics may display too less uptime when you choose a very low frequency (as a very short downtime will be counted as if it lasted until the next execution).

The script outputs the template directly to stdout. You could just pipe this output into a file which then is served by your webserver. Indeed, you probably want to write a small wrapper which pipes the output of the script into a temporary file and then copies the output of that file to the live version. This prevents the live version of the statistics from being blank while the script is running. This wrapper could look like that:

```
#!/bin/sh
/path/to/fetch.py > /tmp/temporary_status
cp /tmp/temporary_status /var/www/html/status.html
rm /tmp/temporary_status
```

You can use only the alerting feature of this script, however the main focus lies on the statistics; so you would probably being better of with an even simpler solution in order to only get email alerts (i.e. the check_host method in the script would likely be all you need for that).

Downtimes overview
------------------

Previous downtimes are displayed by the script if the config key *display_downtimes* is set.

You can specify reasons for downtimes in the configuration by adding a list containing the start (formatted YYYYMMDDHHMM) as first and the reason as second element.

Planned downtimes are not supported yet.

Example
-------

A live example of the statistics page (in german) can be found [here](https://status.profitopia.de).

License
-------

Copyright 2016 Pascal Wichmann

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

   
----------------------------

Scripts and documentation written by Pascal Wichmann, copyright (c) 2016
