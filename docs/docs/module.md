# Writing your own module

If you want to write your own instrumentation or detection module, follow the instructions below.

## Creating the module file tree

you first have to create a new directory into **modules** directory:

```
mkdir modules/hello_world
```

Then, create two text files, respectively named **module.conf** and **module.c**:

```
touch modules/hello_world/module.conf modules/hello_world/module.c
```

## Writing the configuration file

You just have to indicate your module name, its description and the dependencies in the **module.conf** configuration file:
```
name:hello_world
description:First module
dependencies:SCAN
```

## Writing the source code

### Callbacks
Then, you can simply write the source code of your module in **module.c** file !
Oasis allows you to easily execute a callback function when a specific event occurs using the following macros:

* **SCAN_CALLBACK(module_name)** : triggered when a advertising packet is received (Scanning mode)
* **TIME_CALLBACK(module_name)** : triggered every second
* **CONN_RX_CALLBACK(module_name)** : triggered when a connection packet is received (Connected mode)
* **CONN_TX_CALLBACK(module_name)** : triggered when a connection packet is transmitted (Connected mode)
* **CONN_INIT_CALLBACK(module_name)** : triggered when a connection is initiated
* **CONN_DELETE_CALLBACK(module_name)** : triggered when a connection is closed

For example, if you want to execute a specific code when a scan packet is received, use the following code:

```
void SCAN_CALLBACK(hello_world)(metrics_t * metrics) {
  // your code here
}
```


### Metrics
Every callbacks receives as single parameter a pointer to a structure containing all the extracted metrics (type *metrics_t*). This structure is defined as follow:

```
typedef struct metrics {
  packet_t *current_packet;
  connection_t *current_connection;
  local_device_t *local_device;
  remote_device_t *remote_device;
} metrics_t;
```

It includes four pointers to different structures, containing the metrics inferred by the **Core** component:

* **current_packet** : the metrics linked to the current received or transmitted packet
* **current_connection** : the metrics linked to the current connection
* **local_device**: the metrics linked to the local device
* **remote_device** : the metrics linked to the remote device

The current_packet field is a pointer to a *packet_t* structure, allowing to access the timestamp, the CRC validity, the channel, the rssi, the header and the content of the packet. It is defined as follow:

```
typedef struct packet {
  uint32_t timestamp;
  uint16_t valid;
  uint16_t channel;
  uint16_t rssi;
  uint8_t header[2];
  uint8_t content[255];
} packet_t;
```

The **current_connection** field is a pointer to a *connection_t* structure, allowing to access several informations about the connection, such as the Access Address, the CRC init, the Hop Interval, the TX, RX and lost counters and the Channel Map. It is defined as follow:

```
typedef struct connection {
  uint32_t access_address;
  uint32_t crc_init;
  uint16_t hop_interval;
  uint16_t packets_lost_counter;
  uint16_t tx_counter;
  uint16_t rx_counter;
  uint8_t channel_map[5];
} connection_t;
```

The **local_device** field is a pointer to a *local_device_t* structure, indicating the GAP role and the address in use. The **remote_device** field is a pointer to a *remote_device_t* structures, indicating the address type, the GAP role, the address, the advertisements interval and the connection interval. They are defined as follow:

```
typedef enum gap_role {
  ADVERTISER = 0,
  PERIPHERAL = 1,
  SCANNER = 2,
  CENTRAL = 3
} gap_role_t;

typedef struct local_device {
  gap_role_t gap_role;
  uint8_t address[6];
} local_device_t;

typedef struct remote_device {
  address_type_t address_type;
  gap_role_t gap_role;
  uint8_t address[6];
  #ifdef SCAN_ENABLED
  uint32_t advertisements_interval;
  #endif
  #ifdef CONNECTION_ENABLED
  uint32_t connection_interval;
  #endif
} remote_device_t;
```

You can access the fields in these structures from the callbacks. Let us note that sometimes, some information may lack or are not relevant depending on the used callback.

### Memory manipulation

The *Core* component includes a basic memory manipulation library, allowing to dynamically allocate a memory zone or free it. This heap implementation is independent of the memory allocator used by the native controller, and the size of the heap can be controlled in the target configuration file if needed:

```
void * malloc(uint16_t size);
void free(void * p);
```

You can also copy some memory from a location to another one using memcpy:

```
void * memcpy(void *dst, void* src, uint32_t size);
```

The *Core* also implement a hashmap library, allowing to create, manipulate and free a hashmap. Several examples can be found in the detection modules.

### Actions

The native controller can be instrumented from your module using the instrumentation API.

* If you want to start or stop a scanning operation, you can use the following functions:

```
void start_scan();
void stop_scan();
```

### Logging

You can easily log information using the logging system. It mainly exposes the log function:

```
void log(uint8_t *buffer, uint8_t size);
```

In the specific case of a detection module, you can use the alert function, allowing to provide an alert number to identify the module that generated the alert:

```
void alert(uint8_t number, uint8_t *data, size_t data_size);
```

## Testing the module

Select your target:

```
./oasis set-target nexus5
```

Build the embedded software with your new module:

```
./oasis build hello_world
```


Inject the embedded software into the controller memory:

```
./oasis patch
```

Monitor the logs:

```
./oasis interact log
```
