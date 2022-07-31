# Oasis utility

Oasis can be easily manipulated using the oasis script located at the root of the repository. However, it is a simple wrapper aiming at facilitating the use of the framework, you can also use the Makefile.

The general syntax is the following one:

```
./oasis <cmd> [parameters]
```

The following commands are available:

- **targets:** show all targets.
- **set-target:** select the default target.
- **modules:** show all modules.
- **build:** build the embedded software.
- **clean:** clean the build and temporary files.
- **patch:** patch the target with the embedded software.
- **modules:** shows the available modules.
- **interact:** interact with the target.

At any time, you can display help by indicating **--help** parameter, or use a specific target using **--target=**.

## Listing targets

If you want to list every available targets, use:

```
./oasis targets
```

You can also apply a filter if you want to display only some specific targets:

```
./oasis targets cyw
```

## Selecting the default target

If you want to select a specific target, use the **set-target** command:

```
./oasis set-target cyw20735
```

## Listing modules

If you want to list every available modules, use:

```
./oasis modules
```

You can also apply a filter if you want to display only some specific targets:

```
./oasis modules btle
```


## Building the embedded software

If you want to build the embedded software with the modules *btlejuice* and *gattacker*, use:

```
./oasis build btlejuice gattacker
```


## Patching the embedded software

If you want to patch the embedded software, use the following command:

```
./oasis patch
```

## Cleaning the build and temporary files

If you want to clean the build and temporary files, uses:

```
./oasis clean
```

## Interaction with the target

Once the embedded software has been patched, you can easily interact with it from Oasis using **interact** command. The syntax is the following one:

```
oasis interact <subcommand> [parameters]
```

The available subcommands are:

- **read <symbol\>**: read the value in memory of the provided symbol
- **read <address\>**: read the value in memory at the provided address (4 bytes)
- **read <address\> <size\>**: read the value in memory at provided address (variable size)
- **monitor <symbol\>**: display any value modification in memory of the provided symbol
- **monitor <address\>**: display any value modification in memory of the provided address (4 bytes)
- **monitor <address\> <size\>**: display any value modification in memory of the provided address (variable size)
- **log [filename]**: display the log (and copy them in filename if provided) 
- **wireshark [filename]**: monitor the link layer traffic with wireshark (and feed a pcap file if filename is provided)
- **start-scan**: start a scan
- **stop-scan**: stop a scan
- **connect <address\>**: establish a connection with BD address (address type is public)
- **connect <address\> <address_type\>**: establish a connection with BD address (public or random address type)
- **disconnect <handle\>**: disconnect the connection linked to the provided handle

For example, if you want to monitor the log:

```
./oasis interact log
```

Or if you want to track any changes of **toto** symbol:

```
./oasis interact monitor toto
```
