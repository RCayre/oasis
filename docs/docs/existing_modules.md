# Using the existing modules

Oasis provides a set of detection modules, allowing to detect low level Bluetooth Low Energy attacks such as BTLEJack, GATTacker or KNOB.

## Detection modules

The following modules are available:

### jamming
* **Description:** Detection module detecting continuous jamming attack
* **Dependencies:** SCAN

### gattacker
*	**Description:** Detection module detecting GATTacker MiTM attack
*	**Dependencies:** SCAN

### btlejack
*	**Description:** Detection module detecting BTLEJack attack
*	**Dependencies:** CONNECTION

### btlejuice
*	**Description:** Detection module detecting BTLEJuice MiTM attack
*	**Dependencies:** SCAN,CONNECTION

### injectable
*	**Description:** Detection module detecting InjectaBLE attack
*	**Dependencies:** CONNECTION

### knob
*	**Description:** Detection module detecting KNOB attack
*	**Dependencies:** CONNECTION

### monitor_time
*	**Description:** Monitoring module allowing to receive timing events notification
*	**Dependencies:**

### monitor_scan
*	**Description:** Monitoring module allowing to receive LL advertising packets
*	**Dependencies:** SCAN

### monitor_connection
*	**Description:** Monitoring module allowing to receive LL connection packets
*	**Dependencies:** CONNECTION

## Testing a module

If you want to test a specific module, you have to:

- select the target using **set-target** command:

```
./oasis set-target cyw20735
```

- build the embedded software with the selected module using **build** command:

```
./oasis build btlejuice
```

- patch the embedded software previously generated using **patch** command:

```
./oasis patch
```

- monitor the logs using **interact log** command:

```
./oasis interact log
```
