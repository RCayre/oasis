# Introduction
## Presentation

**Oasis** is a lightweight modular framework allowing to easily write, build and patch instrumentation modules for Bluetooth Low Energy (BLE) controllers using standard C language. It has been initially developed in the context of a security-oriented research work aiming at evaluating the feasilibity of building an Intrusion Detection System embedded in BLE controllers. It has been designed to facilitate the development of instrumentation modules using standard C, without requiring any prior knowledge about the underlying architecture.

Currently, the framework provides:

* a generic and modular architecture allowing to focus on the module design without requiring a deep understanding of the targeted controller,
* an automated build system allowing to generate a embedded software easily,
* six lightweight detection modules allowing to detect critical attacks such as BTLEJack, BTLEJuice, GATTacker or Knob,
* a set of user-friendly libraries allowing to facilitate the interaction with the controller,
* support for multiple targets (Raspberry Pi 3+/4, Nexus 5 smartphone, CYW20735 IoT Development Kit, nRF51-based devices),
* a set of automated reverse engineering tools allowing to facilitate the generation of new targets.

## Motivations

This framework has been developed to facilitate the process of reverse engineering, development and patching of a Bluetooth Low Energy controller firmware. Indeed, writing patches for a Bluetooth Low Energy controller is a difficult task: most of the time, the firmwares embedded in such devices are proprietary and requires a significant work of reverse engineering to instrument them. Similarly, they may rely on heterogeneous architectures, perform time-critical operations... This framework aims to facilitate every step of this process by providing a set of tools allowing to write embedded instrumentation modules for common controllers.

The framework allows to generate a lightweight and modular embedded software, which is able to trigger specific actions when a specific event occurs (e.g. packet reception, connection initiation, ...), extract multiple low level characteristics (from the Link Layer traffic to CRC validity) or communicate through an HCI interface. It provides a very powerful way to manipulate the protocol at a very low level without requiring a deep understanding of the underlying architecture as the framework provides a standardized API to the user. These capabilities have initially been used to implement a set of embedded detection modules, allowing to detect multiple Bluetooth Low Energy attacks (e.g. KNOB, BTLEJack, GATTacker...) but it could also be used for other purposes, such as stacks fuzzing or wireless security analysis.

## Documentation
The documentation can be found at https://homepages.laas.fr/rcayre/oasis-documentation

## License

The framework is released under MIT license as an open source software. Pull requests are welcome :)
