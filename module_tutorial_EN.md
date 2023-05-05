# Modules

In DolphinDB, you can save user-defined functions as reusable modules and organize the modules into hierarchical namespaces. Modules can be loaded during the system startup, or imported into a session when needed.

- [Modules](#modules)
	- [1. Overview](#1-overview)
	- [2. Defining a Module](#2-defining-a-module)
		- [2.1 Directory for Module Files](#21-directory-for-module-files)
		- [2.2 Creating a Module File](#22-creating-a-module-file)
		- [2.3 Serializing a Module File](#23-serializing-a-module-file)
	- [3. Importing Modules](#3-importing-modules)
		- [3.1 Importing with `use`](#31-importing-with-use)
		- [3.2 Loading Module Functions as Built-in Functions](#32-loading-module-functions-as-built-in-functions)
	- [4. Organizing Modules](#4-organizing-modules)
		- [4.1 Declaring Namespace for a Module](#41-declaring-namespace-for-a-module)
		- [4.2 Calling Modules with Namespace](#42-calling-modules-with-namespace)
	- [5. Debugging Modules Remotely with GUI](#5-debugging-modules-remotely-with-gui)
	- [6. Rules](#6-rules)
		- [6.1 Calling Module Functions with the Same Name](#61-calling-module-functions-with-the-same-name)
		- [6.2 Reloading a Module](#62-reloading-a-module)
		- [6.3 Cross-module Calls](#63-cross-module-calls)
 

## 1. Overview

A module in DolphinDB is a script file that only contains function definitions. Modules have the following features:

- Module files are located under `[home]/modules` by default.
- A module file has the extension of *.dos* (which stands for “DolphinDB script“) or *.dom*(“DolphinDB module“).
- The first line of a module file must be the module declaration, `module [module_name]`. 
- Except for its first line, a module file only contains module import statements and function definitions.

## 2. Defining a Module

### 2.1 Directory for Module Files

Module files are located at `[home]/modules` by default.

- The `[home]` directory is specified by the configuration parameter *home*, which you can check with `getHomeDir`.  
- The directory for the module files is specified by the configuration parameter *moduleDir*. The default value is the relative path “modules”. The system searches “modules” in the following order: home directory of the node, the working directory of the node, and the directory with the DolphinDB executable. Please note that in the single node mode, these 3 directories are the same by default.

### 2.2 Creating a Module File

Create a file `[module_name].dos` in the “modules” folder, e.g., *fileLog.dos*. The first line must be the module declaration:

```
module fileLog
```

In this example, “fileLog“ is the module name, which must be the same as the name of the module file.

The rest of the file must only contain function definitions (and module import statements, if any). In this example, the “fileLog“ module contains only one function, `appendLog`, which writes log entries to a user-specified file.

```
module fileLog

def appendLog(filePath, logText){
	f = file(filePath,"a+")
	f.writeLine(string(now()) + " : " + logText)
	f.close()
}
```

Note: Besides the module declaration and module import statements, code that is not a part of a function definition will be ignored in a module file.

### 2.3 Serializing a Module File

Use [saveModule](https://dolphindb.com/help/FunctionsandCommands/CommandsReferences/s/saveModule.html) to serialize a *.dos* module file to a binary file with the extension *.dom*. This enhances the security of the code. In this example, we serialize the module file from Section 2.2:

```
saveModule("fileLog")
```

The generated *.dom* file is saved to the same directory as the original *.dos* file.

Note: 

- If the *.dos* file is changed, execute `saveModule` again to generate a new *.dom* file. Set the “overwrite“ parameter to “true“ to replace the old *.dom* file:

```
saveModule("fileLog", ,true)
```

- If a module references another module, the serialization of this module only serializes the referenced module name, and the definition of the referenced module is not serialized. Therefore, when loading or moving a *.dom* file, make sure to load or move the referenced modules as well.

## 3. Importing Modules

### 3.1 Importing with `use` 

You can import a module with the `use` keyword. If the imported module uses other modules, these modules are also loaded automatically. 

Note： 

- The imported modules are only available in the current session. 
- Only module files with the *.dos* extension can be imported with `use`. The binary files (*.dom*) cannot be imported.

After importing the module, you can call the functions defined in the module in the following ways:

- Refer to the module function

```
use fileLog 
appendLog("mylog.txt", "test my log")
```

- Specify the namespace of the function (i.e., the full path of the function under the `modules` directory)

Use this option if there are functions with the same name in other imported modules.

```
use fileLog fileLog::appendLog("mylog.txt", "test my log")
```

### 3.2 Loading Module Functions as Built-in Functions

> Available in version 1.20.1 and later

As mentioned in Section 3.1, the `use` keyword only imports a module to the current session. To make the functions defined in a module available to all sessions, we need to add them as system built-in functions with the function `loadModule` or the configuration parameter *preloadModules*. This also makes the code more concise without the `use` statement, and more convenient for module function references through API calls. 

Both *.dos* files and *.dom* files can be used to load modules. If the “modules” directory contains a “.dos” file and a “.dom” file with the same name, the system will only load the “.dom” file. For a module function imported from a *.dom* file, its definition is not visible to the users. 

Note the following about module dependency when importing a module:

- If you’re loading it from a *.dos* file, the referenced modules are automatically loaded. 
- If you’re loading it from a *.dom* file, the referenced modules must be loaded first.

Note the following about module functions that are added as built-in functions:

- The functions cannot be overridden.
- When the function is referenced by `remoteRun` or `rpc`, its definition will not be serialized and sent to the remote node(s). Therefore, make sure the relevant module has been loaded on the remote node(s) before the remote call or an exception will be thrown.
- The functions have only one copy in the memory and it is visible to all sessions. This saves not only the memory usage but also the time it takes for each session to import the module.  

#### 3.2.1 Using the Function `loadModule` 

`loadModule` can only be used in the initialization script (*dolphindb.dos* as the default file) of the system, and not in the CLI or GUI. For example, to import the module file from Section 2.2, append this line to the initialization script:

```
loadModule("fileLog")
```

When calling a function from the loaded module, specify the namespace of the function (i.e., the full path of the function under the `modules` directory):

```
fileLog::appendLog("mylog.txt", "test my log")
```

#### 3.2.2 Using the Configuration Parameter `preloadModules`

For standalone deployment, specify the modules to be loaded by configuring the parameter *preloadModules* in the configuration file *dolphindb.cfg*; for cluster deployment, configure `preloadModules` in both *controller.cfg* and *cluster.cfg* as the module must be imported to both the controller and the relevant data nodes.

For example:

```
preloadModules=fileLog
```

Use commas to separate multiple modules.

When calling a function from the loaded module, specify the namespace of the function (i.e., the full path of the function under the `modules` directory):

```
fileLog::appendLog("mylog.txt", "test my log")
```

 

#### 3.2.3 Functions Loaded from Modules vs. Function Views 

Note the differences between the built-in functions loaded with `loadModule` or *preloadModules* and the DolphinDB function views:

- The definition of a function view can be viewed by its creator, administrators and users with the required privileges. A module function loaded from a .dom file is more secure as no user can view its definition. 
- Module functions have the module name as their namespace whereas function views don’t have a namespace.
- When the system serializes a module which references a function in another module, the referenced function is only serialized by its name and its definition is not serialized.  A serialized function view, on the other hand, is self-contained with all the referenced objects serialized as well.

Function views and modules are designed for different scenarios. Function views are used in database queries whereas modules usually contain common algorithms or processing logic which can be referenced in different scripts. A function view may reference a function in a module but a module seldom references a function view.

## 4. Organizing Modules

### 4.1 Declaring Namespace for a Module

To organize modules more efficiently, create sub directories under the `modules` directory to create a hierarchy of namespaces for the modules. For example, the modules "fileLog" and "dateUntil" are saved in the paths `modules/system/log/fileLog.dos` and `modules/system/temperal/dateUtil.dos`, respectively. The declaration statements in the first line of the module files should specify the full namespace path, `module system::log::fileLog` and `module system::temperal::dateUtil`.

### 4.2 Calling Modules with Namespace

For a module located at the sub directories under `modules`, specify the full namespace of the module when: 

- Calling the functions `saveModule` and `loadModule`
- Configuring the *preloadModules* parameter
- Importing it with the `use` statement

This example imports the "fileLog" module from the previous section:

```
use system::log::fileLog
```

After the module is imported, you can directly call the function in the module:

```
appendLog("mylog.txt", "test my log")
```

or call the module function with its full namespace:

```
system::log::fileLog::appendLog("mylog.txt", "test my log")
```

Note:

- If there are functions with the same name in other imported modules, call the module function with its full namespace (see section 6.1 Calling Module Functions with the Same Name).
- If the module is loaded with the function `loadModule` or the configuration parameter *preloadModules*, call the module function with its full namespace.

## 5. Debugging Modules Remotely with GUI

When DolphinDB GUI is connected to a remote DolphinDB server, the module edited in GUI must be uploaded to the `modules` directory on the remote server before it is called by the `use` statement.

Since version 0.99.2 of DolphinDB GUI, you can synchronize modules to a remote server by following the steps below:

1. Specify a remote server:

	* Click **Server → Add Server**, and specify the **Remote Directory**.

	![image](./images/GUI/add_server.png)

	* Alternatively, click **Server → Edit Server** to add the remote directory. 

	![image](./images/GUI/module_sync.png)

2. Select the local “modules” directory to launch its menu. Click **Synchronize module to server** to synchronize all files and sub directories under the local “modules” directory to the previously specified remote directory.  

![image](./images/GUI/module_sync.png)

For example, the **Remote Directory** is specified as '[home]/modules', and the file to synchronize is "C:/users/usr1/Project/scripts/test.dos". During the synchronization, the system will generate the directory and the file '[home]/modules/Project/scripts/test.dos' on the remote server.

Once the synchronization is complete, you can import modules with the `use` statement on the remote server. For more information about setting modules directory, see [2.1 Directory for Module Files](#21-directory-for-module-files).

## 6. Rules

### 6.1 Calling Module Functions with the Same Name

Since different modules may contain functions with the same name, it is recommended to call a module function with its namespace. 

For function calls that do not specify the function namespace, DolphinDB disambiguates functions with the same names according to the following rules:

- If one and only one imported module contains the function, it refers to the function defined in that module.
- If two or more imported modules contain the function, throw an exception.

```
Modules [Module1] and [Module2] contain function [functionName]. Please use module name to qualify the function.
```

- If no imported module contains the function, search for system built-in functions; If there is no match, throw an exception.
- If a function in an imported module has the same name as a user-defined function, use the function in the module. If you want to call the user-defined function, specify its namespace. 
  - Note: The default namespace for all user-defined functions and built-in functions is the root directory, indicated by two colons `::` .

In this example, we first create a user-defined function `myfunc`:

```
login("admin","123456")
def myfunc(){
 return 1
}
addFunctionView(myfunc)
```

Next, create a module “sys“ that contains a function also named `myfunc`:

```
module sys
def myfunc(){
 return 3
}
```

Now, if you want to call the function in the module “sys“ in your current session, first import the module with

```
use sys 
```

then call the function with its namespace: 

```
sys::myfunc() 
```

or simply: 

```
myfunc()
```

If you want to call the user-defined function, use:

```
::myfunc()
```

### 6.2 Reloading a Module

Each module is only imported once per session. If you want to repeatedly change a module to test interactively, there are two options:

- Execute the entire module after updating the module.  This method is only effective for the current session.
- [administrators only] Call `clearCachedModules` after updating the module. Then when you import the module with the `use` statement again, the system reloads it from the module file instead of using the cached data, and there is no need to restart the node.

### 6.3 Cross-module Calls

A module can be imported into another module. For example, you can import module A into module B, then import module B into module C. 

However, circular imports are not supported. For example, if module A references functions defined in module B, then module B cannot reference the functions in module A. 





