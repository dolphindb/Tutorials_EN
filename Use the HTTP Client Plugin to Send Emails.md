# Use the HTTP Client Plugin to Send Emails

DolphinDB supports dynamic loading of external plugins written in C++ to enable additional script functions, thus extending system functionality.

This tutorial introduces how to use `sendEmail` in the HTTP Client plugin to send plain text emails.

Steps:

1. Load the HTTP Client plugin in DolphinDB
2. Send the emails

## 1. Load the HTTP Client Plugin in DolphinDB

### Linux

1. Download the plugin files *libPluginHttpClient.so* and *PluginHttpClient.txt*.

> Find the files in the [DolphinDBPlugin](https://github.com/dolphindb/DolphinDBPlugin) project under `/httpClient/bin/linux64/`. Make sure to switch to the branch that is consistent with your server version before downloading.

2. Place *libPluginHttpClient.so* and *PluginHttpClient.txt* in the same directory. Execute the following script to load the plugin:

```
loadPlugin("<PluginDir>/httpClient/bin/linux64/PluginHttpClient.txt");
```

## 2. Send Email

The function `sendEmail` supports sending email to a one or multiple recipients.

### **2.1 Prerequisites**

- To send email using the HTTP Client plugin, enable the SMTP service on your mail account. 
- Use the following function to configure the host and port of your mail account. 

**httpClient::emailSmtpConfig**

```
emailName="example.com";
host="smtp.qq.com";
port=25;
httpClient::emailSmtpConfig(emailName,host,port);
```

### **2.2 httpClient::sendEmail(user,psw,recipient,subject,text)**

where

- *user* is the mail address you use to send the email.
- If an SMTP password is provided, specify *psw* as the SMTP password. Otherwise, it is the password to your mailbox.
- *recipient* indicates the mail address(es) to send the mail to. See examples below.
- *subject* and *text* are the subject and body of the mail.

**Example 1.** Send mail to one recipient

- *recipient* is a string indicating the mail address of the recipient.

```
user='mailFrom@dolphindb.com';
psw='xxxxx';
recipient='mailTo@example.com';
```

Execute `sendEmail`:

```
res=httpClient::sendEmail(user,psw,recipient,'This is a subject','This is a text')
assert  res[`responseCode]==250;
```

Return a dictionary “res“. If the email is sent successfully, `res['responseCode']==250` is returned.

**Example 2. Send to multiple recipients**

- *recipient* is a vector of strings indicating the email addresses of the recipients.

```
user='mailFrom@dolphindb.com';
psw='xxxxx';
recipientCollection='mailToRecipient1@example.com''mailToRecipient2@example.com''mailToRecipient3@example.com';
```

Execute `sendEmail`:

```
res=httpClient::sendEmail(user,psw,recipientCollection,'This is a subject','This is a text');
assert res[`responseCode]==250;
```

Return a dictionary “res“. If the email is sent successfully, `res['responseCode']==250` is returned.















