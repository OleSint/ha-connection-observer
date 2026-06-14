# Connection Observer – Documentación (Español)

**Versión:** 1.3.0  
**Repositorio:** [github.com/OleSint/ha-connection-observer](https://github.com/OleSint/ha-connection-observer)

---

## Tabla de contenidos

1. [¿Qué es Connection Observer?](#1-qué-es-connection-observer)
2. [Cómo funciona](#2-cómo-funciona)
3. [Instalación](#3-instalación)
4. [Asistente de configuración](#4-asistente-de-configuración)
5. [Opciones de configuración](#5-opciones-de-configuración)
   - [Labels de Observer](#labels-de-observer)
   - [Retrasos de alerta por protocolo](#retrasos-de-alerta-por-protocolo)
   - [Watch label – indicadores de desconexión personalizados](#watch-label--indicadores-de-desconexión-personalizados)
6. [Plantillas de notificación](#6-plantillas-de-notificación)
7. [Integración HA Repairs](#7-integración-ha-repairs)
8. [Entidades](#8-entidades)
9. [Servicios](#9-servicios)
10. [Formatos de notificación](#10-formatos-de-notificación)
11. [Casos de uso avanzados](#11-casos-de-uso-avanzados)
12. [Solución de problemas](#12-solución-de-problemas)
13. [Limitaciones conocidas](#13-limitaciones-conocidas)

---

## 1. ¿Qué es Connection Observer?

Connection Observer es una integración personalizada para Home Assistant que monitoriza continuamente la conectividad de tus dispositivos domóticos y te alerta cuando algo se desconecta — antes de que notes que un interruptor ya no responde o que un sensor ha dejado de enviar datos.

**La idea central** es monitorizar por *familia de protocolo* en lugar de por entidad individual. En vez de seleccionar 200 entidades una a una, simplemente eliges "monitorizar todos los dispositivos Zigbee" o "monitorizar todos los dispositivos ESPHome". Cada dispositivo perteneciente a esa familia de integración queda cubierto automáticamente — incluidos los nuevos dispositivos que añadas más adelante.

---

## 2. Cómo funciona

### El estado `unavailable`

Home Assistant dispone de un mecanismo integrado para indicar que un dispositivo ya no es accesible: pone todas las entidades de ese dispositivo en el estado `unavailable`. Esto ocurre automáticamente cuando:

- Un dispositivo Zigbee o Z-Wave deja de responder al coordinador
- Un dispositivo WiFi (ESPHome, Shelly, etc.) ya no es accesible en la red
- Una bombilla Hue se apaga en el interruptor de pared y el puente pierde el contacto
- Cualquier otra integración detecta que la comunicación se ha interrumpido

Connection Observer escucha exactamente esta transición: de cualquier estado → `unavailable`. Cuando la detecta, crea un *evento de desconexión* para el dispositivo afectado.

### Deduplicación a nivel de dispositivo

La mayoría de los dispositivos exponen múltiples entidades en Home Assistant. Una regleta Zigbee puede tener entidades para el estado del interruptor, la potencia actual, la energía total, el voltaje, etc. Cuando esa regleta se desconecta, todas las entidades pasan a `unavailable` al mismo tiempo.

Connection Observer determina a qué *dispositivo* pertenece una entidad a través del registro de dispositivos de HA, y solo crea **un evento por dispositivo** — independientemente de cuántas entidades tenga. Eso significa una notificación por dispositivo, no cinco.

### Protección en el arranque

Cuando Home Assistant se reinicia, todas las integraciones necesitan un momento para reconectar sus dispositivos. Durante esta ventana, muchas entidades pasan brevemente por `unavailable`. Connection Observer espera 60 segundos tras el arranque completo de HA antes de comenzar a rastrear desconexiones. Esto evita una avalancha de falsas alarmas en cada reinicio.

### Almacenamiento persistente

Todos los eventos de desconexión se almacenan en el sistema de almacenamiento integrado de HA (`~/.homeassistant/.storage/`). Los eventos sobreviven a los reinicios y se conservan hasta 30 días.

### Vigilante (Watchdog)

Cada 5 minutos, Connection Observer verifica activamente si los dispositivos con eventos abiertos (es decir, sin reconexión registrada) siguen sin estar disponibles. Si un dispositivo ha vuelto a estar en línea sin producir un evento `state_changed`, el watchdog lo detecta y cierra el evento.

---

## 3. Instalación

### Mediante HACS (recomendado)

1. Asegúrate de que HACS está instalado. Si no, sigue la [guía de instalación de HACS](https://hacs.xyz/docs/setup/download).
2. Abre **HACS → Integraciones** en la barra lateral de HA.
3. Haz clic en el **menú de tres puntos** (arriba a la derecha) → **Repositorios personalizados**.
4. Introduce `https://github.com/OleSint/ha-connection-observer` como URL y selecciona **Integración** como categoría. Haz clic en **Añadir**.
5. Busca **Connection Observer** en la lista de HACS y haz clic en **Descargar**.
6. **Reinicia Home Assistant.**
7. Tras el reinicio, ve a **Ajustes → Dispositivos y servicios → Añadir integración** y busca **Connection Observer**.

### Instalación manual

1. Descarga la última versión desde la [página de releases de GitHub](https://github.com/OleSint/ha-connection-observer/releases).
2. Extrae el archivo y copia la carpeta `custom_components/connection_observer` en tu directorio de configuración de HA bajo `config/custom_components/connection_observer`.
3. **Reinicia Home Assistant.**
4. Tras el reinicio, ve a **Ajustes → Dispositivos y servicios → Añadir integración** y busca **Connection Observer**.

---

## 4. Asistente de configuración

El asistente de configuración te guía a través de seis pasos. Todos los ajustes pueden modificarse posteriormente mediante el botón **Configurar** de la tarjeta de integración.

### Paso 1 – Labels

**Connection Observer ha creado automáticamente tres labels en tu instancia de HA durante la configuración.**

Este paso es puramente informativo — no se requiere ninguna entrada. Simplemente haz clic en Enviar para continuar.

Los labels son inmediatamente visibles en **Ajustes → Etiquetas**:

| Label | Significado |
|---|---|
| `observer_critical` | Crítico – sin retraso, sin cooldown. Alerta inmediata independientemente de todos los ajustes. Marcado con 🔴 en los resúmenes. |
| `observer_watch` | Vigilar – monitorización normal según los ajustes globales. |
| `observer_ignore` | Ignorar – exclusión total de toda monitorización. |

Asigna un label a cualquier entidad del dispositivo deseado — Connection Observer lo detecta inmediatamente, sin reinicio. Detalles en [Sección 5 – Labels de Observer](#labels-de-observer).

### Paso 2 – Protocolos

**Lo que selecciones aquí determina qué dispositivos se monitorizan.**

El asistente solo muestra las familias de integración que están realmente configuradas en tu instancia de HA.

> **Nota:** La selección de protocolos es opcional. Si deseas monitorizar exclusivamente mediante el [sistema de labels](#labels-de-observer), puedes dejar este paso vacío y hacer clic en Enviar.

| Campo | Descripción |
|---|---|
| **Protocolos a monitorizar** | Selección múltiple, opcional. Elige una o más familias de integración. |
| **Idioma de las notificaciones** | Elige English, Deutsch, Français, Nederlands o Español. |

> **Consejo:** Siempre puedes añadir o eliminar protocolos más tarde. Los nuevos dispositivos de un protocolo seleccionado se incluyen automáticamente.

> **Usuarios de Zigbee2MQTT:** Los dispositivos Zigbee2MQTT aparecen en HA bajo el dominio de integración `mqtt` — no existe una entrada separada para Zigbee2MQTT. Selecciona **MQTT** para monitorizarlos. Ten en cuenta que esto también incluirá el resto de dispositivos MQTT de tu instalación (p. ej. Tasmota, sensores personalizados). Para un control más preciso, usa el [sistema de labels](#labels-de-observer): asigna `observer_watch` a los dispositivos MQTT específicos que desees monitorizar.

> ⚠️ **Importante:** Connection Observer solo puede detectar dispositivos cuando HA los pone en `unavailable`. Zigbee2MQTT **no** lo hace por defecto — primero debes activar las comprobaciones de disponibilidad: **Zigbee2MQTT → Ajustes → Disponibilidad → activado**. Sin este ajuste, Connection Observer no puede detectar los dispositivos Z2M sin conexión.

### Paso 3 – Notificaciones

**Configura cómo y cuándo recibir alertas.**

| Campo | Descripción |
|---|---|
| **Servicio(s) de notificación** | Selección múltiple. Elige uno o más servicios `notify.*`. |
| **Notificación inmediata** | Si está activado, se envía una notificación en cuanto un dispositivo se desconecta. Por defecto: **desactivado**. |
| **Resumen programado** | Si está activado, se envía un resumen a la hora configurada. Por defecto: **activado**. |
| **Hora del resumen** | Hora del día para el resumen. |
| **Días del resumen** | Días de la semana para el resumen. Por defecto: todos los días. |
| **Notificar al reconectarse** | Opt-in. Notificación cuando un dispositivo vuelve a estar en línea. Por defecto: **desactivado**. |

### Paso 4 – Prueba

Un paso de prueba opcional envía una notificación a todos tus servicios seleccionados para verificar que todo funciona correctamente.

- Marca **Enviar notificación de prueba ahora** (marcado por defecto) y haz clic en Enviar.
- Desmarca la casilla para omitir este paso.
- Si la prueba falla, se muestra un error. Puedes intentarlo de nuevo o desmarcar la casilla para continuar de todas formas.

### Paso 5 – Avanzado

**Todos los campos son opcionales. El valor 0 desactiva la función correspondiente.**  
El **retraso de alerta global** configurado aquí se aplica a todos los protocolos, salvo que se defina un retraso específico en el Paso 6.

| Campo | Descripción |
|---|---|
| **Retraso de alerta** | Minutos sin conexión antes de crear un evento. Por defecto: **0** (inmediato). |
| **Tiempo mínimo entre notificaciones** | Tiempo mínimo entre notificaciones inmediatas por dispositivo. Por defecto: **0** (sin límite). |
| **Duración mínima sin conexión** | Eventos más cortos que este valor se excluyen del resumen. Por defecto: **0** (todos los eventos). |
| **Incluir habitación / área** | Mostrar el nombre del área de HA en las notificaciones. Por defecto: **desactivado**. |
| **Incluir fabricante y modelo** | Mostrar información del dispositivo. Por defecto: **desactivado**. |
| **Dominios de entidades excluidos** | Excluye dominios de entidades completos (p. ej. `sensor`, `button`). Las entidades `device_tracker` siempre se excluyen automáticamente. |
| **Dispositivos excluidos** | Lista de dispositivos específicos a excluir completamente de la monitorización. Solo se muestran los dispositivos que tienen al menos una entidad en un protocolo configurado — los servicios virtuales (HACS, Supervisor, complementos, etc.) no aparecen. Si se añade un dispositivo mientras está sin conexión, se elimina inmediatamente de la lista de dispositivos sin conexión y cualquier incidencia abierta en HA Repairs se resuelve automáticamente. |

### Paso 6 – Experto

**Ambas funciones son opcionales. Omite este paso si solo necesitas el retraso global.**

#### Retrasos de alerta por protocolo

Cada protocolo que seleccionaste en el Paso 2 aparece aquí con su propio campo de retraso. Un valor de **0** significa "usar el retraso de alerta global del Paso 5". Introduce un valor positivo para anular el retraso global para ese protocolo específico.

**Consejo: Aplicar retrasos recomendados**  
Marca la casilla **Aplicar retrasos recomendados para todos los protocolos** y haz clic en Enviar. Todos los campos de retraso se rellenan automáticamente con los valores recomendados. Puedes ajustar los valores individuales o aceptarlos tal como están.

Los valores recomendados se basan en las características de conexión típicas de cada familia de protocolos:
- Protocolos TCP directos (ESPHome, Shelly, Tasmota) → **2 min** (conexión persistente, detección rápida)
- Protocolos mesh locales (ZHA, Z-Wave JS) → **5 min** (el enrutamiento mesh necesita un momento)
- BLE pasivo (BTHome, GARDENA Bluetooth) → **20 min** (ciclos de anuncio infrecuentes)
- Protocolos cloud (Tuya, Nest, Ring…) → **10 min** (latencia de sondeo)

Consulta la [tabla de referencia completa](#retrasos-de-alerta-por-protocolo) en la Sección 5 para ver todos los valores.

#### Watch label – indicadores de desconexión personalizados

Introduce aquí el nombre de una etiqueta de HA (p. ej. `indicador_desconexion`). Cualquier entidad a la que asignes esta etiqueta en el editor de etiquetas de Home Assistant será tratada como un indicador de desconexión personalizado por Connection Observer:

- Cuando el estado de la entidad cambia a **`on`** → Connection Observer crea un evento de desconexión (protocolo mostrado como `custom`)
- Cuando el estado de la entidad cambia a **`off`** → Connection Observer marca el dispositivo como de nuevo en línea

Esta función es intencionadamente genérica: etiqueta cualquier entidad que desees — un sensor binario de plantilla, un helper o cualquier entidad binaria — y Connection Observer reaccionará a sus cambios de estado.

**Caso de uso típico:** los dispositivos BLE pasivos (sensores BTHome, GARDENA Bluetooth) no pueden monitorizarse en tiempo real mediante el estado `unavailable`. Consulta las [Limitaciones conocidas](#13-limitaciones-conocidas) y el [Watch label](#watch-label--indicadores-de-desconexión-personalizados) en la Sección 5 para un ejemplo completo paso a paso.

---

## 5. Opciones de configuración

Todos los ajustes del asistente pueden modificarse en cualquier momento mediante **Ajustes → Dispositivos y servicios → Connection Observer → Configurar**.

Además de los ajustes del asistente, la página de opciones también ofrece:

### Notificación de prueba

Desde la página de opciones puedes enviar una notificación de prueba en cualquier momento sin necesidad de reconfigurar la integración. Marca **Enviar notificación de prueba ahora** para enviar un mensaje de prueba a todos tus servicios configurados antes de guardar los nuevos ajustes.

### Dominios de entidades excluidos

Puedes excluir dominios de entidades completos de la monitorización — p. ej. `sensor`, `button`, `number`. Esto resulta útil cuando ciertos dominios pasan por `unavailable` con frecuencia en tu configuración. Las entidades `device_tracker` siempre se excluyen automáticamente, independientemente de este ajuste.

### Umbral de HA Repairs

Define el número de horas que un dispositivo debe estar sin conexión antes de que se cree una incidencia persistente en **Ajustes → Reparaciones**. El valor `0` desactiva esta función. Por defecto: **24 horas**.

Consulta la [Sección 7](#7-integración-ha-repairs) para más detalles.

### Plantillas de notificación

Siete campos de texto opcionales permiten personalizar el formato de cualquier notificación. Deja un campo vacío para usar el texto predeterminado según el idioma.

Consulta la [Sección 6](#6-plantillas-de-notificación) para más detalles.

### Labels de Observer

Connection Observer crea automáticamente tres labels en Home Assistant durante la configuración. Son inmediatamente visibles en **Ajustes → Etiquetas** y pueden asignarse a cualquier entidad — sin reinicio, sin cambios de configuración.

| Label | Color | Comportamiento |
|---|---|---|
| `observer_critical` | 🔴 Rojo | Sin retraso, sin cooldown — alerta inmediata independientemente de todos los ajustes globales. Marcado con 🔴 en los resúmenes. Omite el búfer de flood. |
| `observer_watch` | 🔵 Azul | Monitorización normal según los ajustes globales (retraso, cooldown, etc.). |
| `observer_ignore` | ⚫ Gris | Exclusión total — el dispositivo es completamente ignorado por Connection Observer. |

**Prioridad:** `observer_ignore` > `observer_critical` > `observer_watch` > monitorización basada en protocolo

**Conflictos:** Si un dispositivo tiene tanto `observer_ignore` como `observer_critical` o `observer_watch`, `observer_ignore` siempre prevalece. Aparece una advertencia en el próximo resumen.

**Propiedades clave:**
- Un label en **cualquier entidad** del dispositivo es suficiente — todo el dispositivo se trata en consecuencia.
- Los labels surten efecto **inmediatamente** e **independientemente de la selección de protocolos**.
- Los dispositivos pueden estar cubiertos tanto por protocolos como por labels simultáneamente — el label tiene prioridad.

> **Consejo:** Asigna `observer_critical` a dispositivos críticos (detectores de agua, detectores de humo), usa `observer_ignore` para silenciar dispositivos ruidosos y `observer_watch` para monitorizar un dispositivo individual sin activar todo un protocolo.

### Retrasos de alerta por protocolo

Cada protocolo seleccionado puede tener su propio retraso de alerta que anula el valor global. Establece el retraso de un protocolo en **0** (o déjalo sin configurar) para usar el retraso global.

**Configuración con un clic:** En el paso Experto (asistente) o la página Experto (opciones), marca **Aplicar retrasos recomendados** y haz clic en Enviar. Todos los campos se rellenan automáticamente.

| Protocolo | Dominio | Retraso recomendado | Razón |
|---|---|---:|---|
| Zigbee (ZHA) | `zha` | 5 min | El enrutamiento mesh necesita un momento |
| Zigbee (deCONZ) | `deconz` | 5 min | El enrutamiento mesh necesita un momento |
| Z-Wave (Z-Wave JS) | `zwave_js` | 5 min | El enrutamiento mesh necesita un momento |
| Matter | `matter` | 5 min | Comportamiento similar a mesh |
| Thread (OTBR) | `otbr` | 5 min | Mesh Thread |
| Bluetooth | `bluetooth` | 10 min | La conexión BLE es más lenta |
| BTHome | `bthome` | 20 min | BLE pasivo – anuncios poco frecuentes |
| RFXtrx (433 MHz) | `rfxtrx` | 10 min | RF unidireccional, sin confirmación |
| MySensors | `mysensors` | 10 min | Sondeo lento |
| Insteon | `insteon` | 5 min | Bus propietario, basado en sondeo |
| KNX | `knx` | 5 min | Bus cableado, fiable pero sondeado |
| Velbus | `velbus` | 5 min | Bus cableado |
| ESPHome | `esphome` | 2 min | TCP persistente, detección muy rápida |
| Shelly | `shelly` | 2 min | TCP persistente, detección muy rápida |
| Tasmota | `tasmota` | 2 min | TCP persistente, detección muy rápida |
| Tuya | `tuya` | 5 min | Sondeo cloud |
| WLED | `wled` | 2 min | TCP local |
| TP-Link (Kasa/Tapo) | `tplink` | 3 min | TCP local |
| TP-Link Omada | `tplink_omada` | 3 min | TCP local |
| Broadlink | `broadlink` | 3 min | TCP local |
| Philips Hue | `hue` | 3 min | Puente Hue local |
| IKEA TRÅDFRI | `tradfri` | 5 min | El hub IKEA puede ser lento |
| LIFX | `lifx` | 3 min | UDP/TCP local |
| Nanoleaf | `nanoleaf` | 3 min | TCP local |
| Yeelight | `yeelight` | 2 min | TCP local |
| Xiaomi Mi Home | `xiaomi_miio` | 5 min | Mezcla local + cloud |
| Sonos | `sonos` | 3 min | Red local |
| Google Cast | `cast` | 3 min | Red local |
| Logitech Media Server | `squeezebox` | 5 min | Depende del servidor |
| Kodi | `kodi` | 3 min | Red local |
| Plex | `plex` | 5 min | Depende del servidor |
| Sony Bravia TV | `braviatv` | 3 min | Red local |
| Samsung TV | `samsungtv` | 3 min | Red local |
| LG webOS TV | `webostv` | 3 min | Red local |
| Android TV / Google TV | `androidtv` | 3 min | Red local |
| Apple TV | `apple_tv` | 3 min | Red local |
| Roku | `roku` | 3 min | Red local |
| Yamaha MusicCast | `yamaha_musiccast` | 3 min | Red local |
| Denon / Marantz AVR | `denon` | 3 min | Red local |
| Onkyo / Pioneer AVR | `onkyo` | 3 min | Red local |
| Logitech Harmony | `harmony` | 5 min | Requiere hub |
| Netatmo | `netatmo` | 10 min | Sondeo cloud, alta latencia |
| Tado | `tado` | 10 min | Sondeo cloud |
| Daikin | `daikin` | 5 min | Mezcla local + cloud |
| ecobee | `ecobee` | 10 min | Sondeo cloud |
| Google Nest | `nest` | 10 min | Sondeo cloud |
| HomeWizard Energy | `homewizard` | 3 min | LAN local |
| Tibber | `tibber` | 10 min | API cloud |
| SMA Solar | `sma` | 10 min | Cloud / Modbus local |
| SolarEdge | `solaredge` | 10 min | Sondeo cloud |
| Fronius | `fronius` | 10 min | Sondeo cloud |
| Tesla Powerwall | `powerwall` | 5 min | Generalmente local |
| Nuki Smart Lock | `nuki` | 5 min | Puente BLE / cloud |
| August Smart Lock | `august` | 5 min | Cloud |
| Yale Smart Alarm | `yale_smart_alarm` | 5 min | Cloud |
| Ring | `ring` | 10 min | Cámara cloud |
| Blink | `blink` | 10 min | Cámara cloud |
| Arlo | `arlo` | 10 min | Cámara cloud |
| DoorBird | `doorbird` | 3 min | LAN local |
| Reolink | `reolink` | 3 min | LAN local |
| Amcrest | `amcrest` | 3 min | LAN local |
| Eufy Security | `eufy_security` | 5 min | Cloud |
| SimpliSafe | `simplisafe` | 10 min | Cloud |
| Abode | `abode` | 10 min | Cloud |
| UniFi (Ubiquiti) | `unifi` | 3 min | LAN local |
| AVM FRITZ!Box | `fritz` | 5 min | LAN local |
| MikroTik | `mikrotik` | 3 min | LAN local |
| ASUS Router | `asusrouter` | 3 min | LAN local |
| Synology NAS | `synology_dsm` | 3 min | LAN local |
| Viessmann ViCare | `vicare` | 10 min | Cloud |
| Vaillant (myVaillant) | `vaillant` | 10 min | Cloud |
| Bosch Smart Home | `bosch_shc` | 5 min | Controlador local |
| Mitsubishi MelCloud | `melcloud` | 10 min | Cloud |
| NIBE heat pump | `nibe_heatpump` | 10 min | Cloud / local |
| Huawei Solar | `huawei_solar` | 5 min | Modbus local |
| Enphase Envoy | `enphase_envoy` | 5 min | LAN local |
| GoodWe | `goodwe` | 10 min | Cloud |
| Growatt | `growatt_server` | 10 min | Cloud |
| EcoFlow | `ecoflow` | 10 min | Cloud |
| Roborock | `roborock` | 3 min | Local + cloud |
| ECOVACS | `ecovacs` | 5 min | Cloud |
| Neato Robotics | `neato` | 5 min | Cloud |
| LG ThinQ | `lg_thinq` | 5 min | Cloud |
| Meross | `meross` | 3 min | Local + cloud |
| Belkin WeMo | `wemo` | 3 min | LAN local |
| myQ (Chamberlain / LiftMaster) | `myq` | 5 min | Cloud |
| Nice G.O. | `nice_go` | 5 min | Cloud |
| Ecowitt | `ecowitt` | 10 min | Local, raramente crítico |
| Ambient Weather Station | `ambient_station` | 10 min | Cloud / local |
| Husqvarna Automower | `husqvarna_automower` | 10 min | Cloud |
| GARDENA Bluetooth | `gardena_bluetooth` | 20 min | BLE pasivo |
| MQTT | `mqtt` | 5 min | Ajustar por dispositivo – muy variable |
| HomeKit Controller | `homekit_controller` | 5 min | HomeKit local |
| Lutron Caséta | `lutron_caseta` | 3 min | Puente local |
| SwitchBot | `switchbot` | 10 min | BLE / cloud |
| iRobot Roomba | `roomba` | 5 min | Cloud |

> ⚠️ **Para desarrolladores:** Cada vez que se añada un nuevo protocolo a `KNOWN_PROTOCOLS` en `const.py`, **se debe** añadir un retraso recomendado correspondiente a `PROTOCOL_DELAY_HINTS` en el mismo archivo, y añadir una nueva fila a esta tabla en los cinco archivos de documentación.

---

### Watch label – indicadores de desconexión personalizados

La función **watch label** permite monitorizar *cualquier* dispositivo que Connection Observer no pueda monitorizar mediante la ruta estándar `unavailable` — por ejemplo:

- **Sensores BLE pasivos** (BTHome, GARDENA Bluetooth): sin conexión persistente, HA solo establece `unavailable` al cabo de horas
- **Dispositivos cloud** que permanecen "disponibles" aunque el dispositivo físico esté averiado o sea inaccesible
- **Cualquier escenario personalizado** en el que puedas construir un sensor binario que refleje el estado real de la conexión

#### Cómo funciona

1. Crea un **sensor binario de plantilla** (o cualquier entidad binaria) que se active con `on` cuando tu dispositivo está sin conexión y `off` cuando está en línea.
2. En el editor de etiquetas de HA (**Ajustes → Etiquetas**), crea una etiqueta con el nombre exacto que configuraste en el paso Experto (p. ej. `indicador_desconexion`).
3. Asigna esa etiqueta a tu sensor binario de plantilla.
4. Connection Observer recoge automáticamente todas las entidades que llevan la etiqueta y monitoriza su estado:
   - `on` → crea un evento de desconexión (protocolo mostrado como `custom`)
   - `off` → marca el dispositivo como de nuevo en línea

#### Ejemplo: monitor de actualización para sensor de puerta BTHome

Crea un sensor binario de plantilla que compruebe si la última actualización fue hace más de 2 horas:

```yaml
# configuration.yaml
template:
  - binary_sensor:
      - name: "BTHome Puerta Indicador Sin Conexión"
        unique_id: bthome_puerta_indicador_sin_conexion
        state: >
          {{ (now() - states.sensor.bthome_puerta_contacto.last_updated).total_seconds() > 7200 }}
        device_class: problem
```

A continuación:
1. Ve a **Ajustes → Etiquetas** → crea una etiqueta llamada `indicador_desconexion`
2. Ve a **Ajustes → Dispositivos y servicios → Entidades** → busca `binary_sensor.bthome_puerta_indicador_sin_conexion` → asigna la etiqueta `indicador_desconexion`
3. En el paso Experto de Connection Observer, establece **Watch label** como `indicador_desconexion`

Connection Observer creará ahora un evento de desconexión cada vez que el sensor BTHome no haya enviado un informe en más de 2 horas, y lo cerrará automáticamente cuando llegue un nuevo informe.

> **Consejo:** Puedes etiquetar varias entidades con el mismo watch label. Cada una se monitoriza de forma independiente. El nombre del dispositivo en las notificaciones es el nombre descriptivo de la entidad etiquetada.

---

### Configuración inicial recomendada

- **Notificación inmediata:** desactivada
- **Resumen:** activado, diario a las 08:00
- **Retraso de alerta:** 5 minutos global (evita falsas alarmas por caídas breves de WiFi)
- **Retrasos por protocolo:** usa "Aplicar retrasos recomendados" para una configuración rápida
- **Duración mínima sin conexión:** 5 minutos (mantiene el resumen limpio)
- **Incluir área:** activado (hace las notificaciones mucho más legibles)
- **Umbral HA Repairs:** 24 horas
- **Watch label:** configúralo para dispositivos BLE pasivos o personalizados que quieras monitorizar

---

## 6. Plantillas de notificación

Connection Observer envía tres tipos de notificaciones: inmediata (desconexión), reconexión y resumen. Cada tipo tiene un título y un cuerpo de mensaje que pueden personalizarse de forma independiente.

### Plantillas disponibles

Todos los campos de plantilla se encuentran en **Ajustes → Dispositivos y servicios → Connection Observer → Configurar**, al final de la página de opciones.

| Clave de plantilla | Se aplica a | Variables disponibles |
|---|---|---|
| `tmpl_imm_title` | Notificación inmediata – título | `{device_name}` `{protocol}` `{time}` `{area}` `{model}` |
| `tmpl_imm_msg` | Notificación inmediata – mensaje | `{device_name}` `{protocol}` `{time}` `{area}` `{model}` |
| `tmpl_rec_title` | Reconexión – título | `{device_name}` |
| `tmpl_rec_msg` | Reconexión – mensaje | `{device_name}` |
| `tmpl_sum_title` | Resumen – título | `{count}` |
| `tmpl_sum_resolved` | Resumen – línea para evento resuelto | `{device_name}` `{area}` `{protocol}` `{time_offline}` `{time_online}` |
| `tmpl_sum_ongoing` | Resumen – línea para dispositivo aún sin conexión | `{device_name}` `{area}` `{protocol}` `{time_offline}` |

### Notas sobre las variables

- `{area}` está preformateado como ` [Nombre del área]` (con un espacio inicial) cuando la opción *incluir área* está activada, o como cadena vacía en caso contrario.
- `{model}` es `Fabricante – Modelo` o vacío.
- `{time}` / `{time_offline}` / `{time_online}` tienen el formato `HH:MM`. Para `{time_offline}` en el resumen, la fecha se incluye como `MM/DD HH:MM`.

### Notas importantes

- Si estableces un `tmpl_imm_msg` personalizado, la segunda línea automática con zona y modelo (📍 …) **no** se añade. Incluye `{area}` y `{model}` en tu plantilla si deseas esa información.
- Los errores de plantilla (p. ej. un error tipográfico en el nombre de una variable) se registran como advertencias.

---

## 7. Integración HA Repairs

Cuando un dispositivo lleva más tiempo sin conexión que el umbral configurado (por defecto: 24 horas), Connection Observer crea una incidencia persistente en **Ajustes → Reparaciones**. Esto complementa las notificaciones habituales.

### Qué muestra la incidencia

La entrada indica:
- El nombre del dispositivo
- El protocolo / la integración
- La marca de tiempo desde que el dispositivo está sin conexión

### Resolución automática

Cuando el dispositivo vuelve a estar en línea — mediante un evento `state_changed` o mediante el watchdog — la incidencia se **elimina automáticamente**.

### Desactivación

Establece **Incidencia en HA Repairs tras N horas sin conexión** en `0` en las opciones.

---

## 8. Entidades

Connection Observer crea tres entidades por instancia de integración.

### `sensor.connection_observer_offline_devices`

**Tipo:** Sensor | **Unidad:** devices | **Icono:** `mdi:lan-disconnect`

Muestra el número de dispositivos que están actualmente sin conexión.

**Atributos de estado:**

| Atributo | Descripción |
|---|---|
| `devices` | Lista plana de nombres de dispositivos actualmente sin conexión. |
| `by_protocol` | Desglose por protocolo: número sin conexión y lista detallada de dispositivos por familia de integración. |

El atributo `by_protocol` tiene la siguiente estructura:

```yaml
by_protocol:
  shelly:
    offline: 1
    devices:
      - name: "Enchufe Cocina"
        offline_since: "22.05. 14:30"
        offline_duration: "2h 15m"
  bthome:
    offline: 0
    devices: []
```

Solo aparecen en este atributo los protocolos con al menos un dispositivo actualmente sin conexión.

**Ejemplo — tarjeta Markdown con estado por protocolo:**
```yaml
type: markdown
content: >
  {% set proto = state_attr('sensor.connection_observer_offline_devices', 'by_protocol') %}
  {% for p, data in proto.items() %}
  **{{ p }}**: {{ data.devices | map(attribute='name') | join(', ') }}
  (sin conexión desde {{ data.devices[0].offline_since }})
  {% endfor %}
```

**Ejemplo en una automatización:**
```yaml
condition:
  - condition: numeric_state
    entity_id: sensor.connection_observer_offline_devices
    above: 0
```

---

### `sensor.connection_observer_pending_summary_events`

**Tipo:** Sensor | **Unidad:** events | **Icono:** `mdi:clock-alert-outline`

Muestra el número de eventos de desconexión que aún no se han incluido en un resumen. Se reinicia a 0 tras el envío de un resumen o tras `clear_history`.

---

### `sensor.connection_observer_event_history`

**Tipo:** Sensor | **Unidad:** events | **Icono:** `mdi:history`

Muestra el número total de eventos de desconexión almacenados.

**Atributo de estado `events`:** Lista de los últimos 100 eventos, del más reciente al más antiguo.

Cada entrada contiene: `device_name`, `area`, `protocol`, `disconnected_at`, `reconnected_at`, `still_offline`, `is_critical`.

Diseñado para tarjetas de panel como **flex-table-card** o **mushroom-template-card**.

---

### `binary_sensor.connection_observer_connection_problem`

**Tipo:** Sensor binario | **Clase:** `problem` | **Icono:** `mdi:check-network`

- **`ON`** – al menos un dispositivo está actualmente sin conexión
- **`OFF`** – todos los dispositivos monitorizados son accesibles

**Ejemplo – alerta si el problema persiste más de 10 minutos:**
```yaml
trigger:
  - platform: state
    entity_id: binary_sensor.connection_observer_connection_problem
    to: "on"
    for:
      minutes: 10
action:
  - service: notify.mobile_app_phone
    data:
      message: "¡Un dispositivo lleva más de 10 minutos sin conexión!"
```

---

## 9. Servicios

### `connection_observer.send_summary_now`

Envía inmediatamente un resumen de todos los eventos de desconexión pendientes. Tras la llamada, todos los eventos pendientes quedan marcados como incluidos en un resumen.

```yaml
service: connection_observer.send_summary_now
```

---

### `connection_observer.clear_history`

Borra todos los eventos almacenados de la memoria y del almacenamiento persistente. También elimina todas las incidencias abiertas de HA Repairs.

> ⚠️ Esta acción es irreversible.

```yaml
service: connection_observer.clear_history
```

---

### `connection_observer.clear_device`

Borra todos los eventos de desconexión almacenados para un dispositivo específico y elimina su incidencia de HA Repairs correspondiente. Útil cuando un dispositivo ha sido reemplazado o cuando quieres restablecer el historial de un solo dispositivo sin borrar todo el historial.

| Parámetro | Descripción |
|---|---|
| `entity_id` | Obligatorio. Un ID de entidad perteneciente al dispositivo que se desea restablecer (p. ej. `sensor.enchufe_salon_energy`). |

```yaml
service: connection_observer.clear_device
data:
  entity_id: sensor.enchufe_salon_energy
```

---

## 10. Formatos de notificación

### Notificación inmediata

**Básica:**
> **Conexión perdida**
> ⚠️ Enchufe Salón (shelly) perdió la conexión a las 14:32.

**Con área e información de dispositivo activadas:**
> **Conexión perdida**
> ⚠️ Enchufe Salón (shelly) perdió la conexión a las 14:32.
> 📍 Salón  ·  Shelly Plus 1PM

### Notificación de reconexión (opt-in)

> **Conexión restaurada**
> ✅ Enchufe Salón está de nuevo en línea.

### Notificación agrupada ante fallos simultáneos (≥ 5 dispositivos)

Cuando 5 o más dispositivos se desconectan en 5 segundos, se envía una sola notificación agrupada en lugar de alertas individuales. Esto evita una avalancha de notificaciones durante reinicios del router o breves cortes de infraestructura.

**Fallo de conexión:**
> **Fallo de conexión – 8 dispositivos**
> ⚠️ 8 dispositivos sin conexión simultáneamente — probable problema de infraestructura (p. ej. reinicio del router).
> • Enchufe Salón (shelly)
> • Sensor Cocina (zha)
> • Lámpara Pasillo (hue)
> • Bombilla Dormitorio (hue)
> • Interruptor Oficina (esphome)
> • …

**Reconexión:**
> **Conexión restaurada – 8 dispositivos**
> ✅ 8 dispositivos de nuevo en línea:
> • Enchufe Salón
> • Sensor Cocina
> • Lámpara Pasillo
> • Bombilla Dormitorio
> • Interruptor Oficina
> • …

Si hay menos de 5 dispositivos afectados, se envían notificaciones individuales como de costumbre (incluida la comprobación del cooldown).

### Resumen

> **Resumen de conexiones**
> 📋 3 dispositivo(s) afectado(s) desde el último resumen:
> • 🔴 Detector de agua Sótano [Sótano] (zha): sin conexión desde 05/19 07:15, de nuevo en línea a las 07:42
> • Bombilla Dormitorio [Dormitorio] (hue): sin conexión desde 05/19 09:05 ⚠️ todavía sin conexión
> • Detector Pasillo (esphome): sin conexión desde 05/19 11:20, de nuevo en línea a las 11:28

El prefijo 🔴 indica dispositivos con el label `observer_critical`.

---

## 11. Casos de uso avanzados

### Usar los modos inmediato y resumen simultáneamente

Activa ambos modos:
- **Retraso de alerta** de 3 a 5 minutos para ignorar cortes breves
- **Notificación inmediata** para conciencia en tiempo real
- **Resumen** para una visión general diaria
- **Duración mínima sin conexión** de 5 minutos para mostrar solo eventos significativos

### Combinación con automatizaciones de HA

```yaml
# Anunciar dispositivos sin conexión por TTS si siguen offline a la hora de dormir
trigger:
  - platform: time
    at: "22:00:00"
condition:
  - condition: state
    entity_id: binary_sensor.connection_observer_connection_problem
    state: "on"
action:
  - service: tts.speak
    data:
      message: >
        Atención: {{ states('sensor.connection_observer_offline_devices') }}
        dispositivo(s) están actualmente sin conexión.
```

### Enviar a múltiples servicios

Selecciona varios servicios en el campo de servicio de notificación. Todos reciben cada notificación simultáneamente.

### Excluir una entidad específica

Añádelo a la lista *Dispositivos excluidos* en los ajustes avanzados. Todas las entidades de ese dispositivo serán ignoradas. Si el dispositivo está sin conexión en el momento de guardar, se elimina inmediatamente de la lista de dispositivos sin conexión y cualquier incidencia abierta en HA Repairs se resuelve automáticamente.

### Control granular con los labels de Observer

El sistema de labels permite excepciones por dispositivo sin abrir la configuración:

**Dispositivo crítico (p. ej. detector de agua, detector de humo):**  
Asigna `observer_critical` a una entidad del dispositivo → alerta inmediata sin retraso ni cooldown, 🔴 en los resúmenes.

**Excluir temporalmente un dispositivo (p. ej. durante obras):**  
Asigna `observer_ignore` → el dispositivo queda totalmente silenciado. Elimina el label cuando terminen las obras.

**Monitorizar un solo dispositivo MQTT sin activar todo el protocolo MQTT:**  
Asigna `observer_watch` → solo ese dispositivo es monitorizado.

---

## 12. Solución de problemas

### No se envían notificaciones

1. Comprueba que hay un servicio de notificación seleccionado en **Configurar**.
2. Prueba tu servicio notify directamente en **Herramientas de desarrollador → Servicios**.
3. Revisa el registro de HA en busca de errores de `connection_observer`.
4. Asegúrate de que **Notificación inmediata** o **Resumen programado** están activados.

### El resumen no se envía

1. Comprueba que **Resumen programado** está activado.
2. Verifica la hora y los días del resumen en **Configurar**.
3. Revisa `sensor.connection_observer_pending_summary_events` — si es 0, no hay eventos pendientes.
4. Revisa el registro de HA.

### Los dispositivos aparecen sin conexión tras un reinicio de HA

Esto no debería ocurrir gracias al período de gracia de 60 segundos. Si ocurre:
- El dispositivo puede estar genuinamente sin conexión.
- Si el estado en HA no es `unavailable`, el watchdog corregirá el evento en 5 minutos.

### Un dispositivo aparece sin conexión pero funciona bien en HA

El watchdog se ejecuta cada 5 minutos y cerrará el evento automáticamente. También puedes llamar a `clear_history` para restablecer inmediatamente.

### La incidencia de HA Repairs no se creó

1. Comprueba que el umbral no está en `0`.
2. El dispositivo debe llevar sin conexión más tiempo que el umbral. El watchdog crea la incidencia en su siguiente ejecución (cada 5 minutos).

### Advertencia «La unidad de medida no puede convertirse» tras actualizar a v1.3.0

Al arrancar por primera vez tras la actualización a v1.3.0, HA puede mostrar una advertencia para `sensor.connection_observer_event_history`: la unidad `events` difiere de la unidad vacía almacenada anteriormente.

**Solución:** Elige **«Corregir estadísticas»** en el diálogo de advertencia — no «Eliminar». HA solo corrige la entrada de unidad en la base de datos; no se pierde ningún valor de medición.

---

## 13. Limitaciones conocidas

- **Integraciones solo en la nube:** Es posible que los dispositivos conectados exclusivamente a través de un servicio en la nube no se detecten si la integración no establece `unavailable` cuando la nube no está disponible.
- **Integraciones por sondeo:** Una desconexión puede detectarse solo después del siguiente ciclo de sondeo.
- **Dispositivos BLE pasivos (BTHome etc.):** Los sensores Bluetooth Low Energy como los sensores de puerta/ventana BTHome no mantienen una conexión persistente — emiten anuncios periódicos. Si un dispositivo de este tipo se desconecta (p. ej. se retira la batería), Home Assistant solo establece sus entidades como `unavailable` tras su propio tiempo de espera interno, que puede ser de varias horas. Connection Observer solo puede reaccionar cuando HA informa `unavailable`. Por tanto, la monitorización en tiempo real no es estructuralmente posible para dispositivos BLE pasivos, a diferencia de los dispositivos WiFi. **Solución desde v1.1.0:** Usa la función [Watch label](#watch-label--indicadores-de-desconexión-personalizados) con un sensor binario de plantilla que monitorice `last_updated` — esto permite la detección en cuestión de minutos.
- **Zigbee2MQTT – comprobación de disponibilidad obligatoria:** Connection Observer reacciona al estado `unavailable` de las entidades. Zigbee2MQTT **no** establece este estado por defecto — las comprobaciones de disponibilidad deben activarse en Z2M: **Ajustes → Disponibilidad → activado**. Sin este ajuste, los dispositivos Z2M no se detectarán.
- **Una sola instancia:** Connection Observer admite una única instancia de integración por instalación de HA.
- **Retención de eventos 30 días:** Los eventos con más de 30 días se eliminan automáticamente del almacenamiento.
