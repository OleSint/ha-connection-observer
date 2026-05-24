# Connection Observer – Documentación (Español)

**Versión:** 1.0.1  
**Repositorio:** [github.com/OleSint/ha-connection-observer](https://github.com/OleSint/ha-connection-observer)

---

## Tabla de contenidos

1. [¿Qué es Connection Observer?](#1-qué-es-connection-observer)
2. [Cómo funciona](#2-cómo-funciona)
3. [Instalación](#3-instalación)
4. [Asistente de configuración](#4-asistente-de-configuración)
5. [Opciones de configuración](#5-opciones-de-configuración)
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

El asistente de configuración te guía a través de cuatro pasos. Todos los ajustes pueden modificarse posteriormente mediante el botón **Configurar** de la tarjeta de integración.

### Paso 1 – Protocolos

**Lo que selecciones aquí determina qué dispositivos se monitorización.**

El asistente solo muestra las familias de integración que están realmente configuradas en tu instancia de HA.

| Campo | Descripción |
|---|---|
| **Protocolos a monitorizar** | Selección múltiple. Elige una o más familias de integración. |
| **Idioma de las notificaciones** | Elige English, Deutsch, Français, Nederlands o Español. |

> **Consejo:** Siempre puedes añadir o eliminar protocolos más tarde. Los nuevos dispositivos de un protocolo seleccionado se incluyen automáticamente.

> **Usuarios de Zigbee2MQTT:** Los dispositivos Zigbee2MQTT aparecen en HA bajo el dominio de integración `mqtt` — no existe una entrada separada para Zigbee2MQTT. Selecciona **MQTT** para monitorizarlos. Ten en cuenta que esto también incluirá el resto de dispositivos MQTT de tu instalación (p. ej. Tasmota, sensores personalizados). Para un control más preciso, el filtrado por etiquetas (labels) está previsto para una versión futura.

### Paso 2 – Notificaciones

**Configura cómo y cuándo recibir alertas.**

| Campo | Descripción |
|---|---|
| **Servicio(s) de notificación** | Selección múltiple. Elige uno o más servicios `notify.*`. |
| **Notificación inmediata** | Si está activado, se envía una notificación en cuanto un dispositivo se desconecta. Por defecto: **desactivado**. |
| **Resumen programado** | Si está activado, se envía un resumen a la hora configurada. Por defecto: **activado**. |
| **Hora del resumen** | Hora del día para el resumen. |
| **Días del resumen** | Días de la semana para el resumen. Por defecto: todos los días. |
| **Notificar al reconectarse** | Opt-in. Notificación cuando un dispositivo vuelve a estar en línea. Por defecto: **desactivado**. |

### Paso 3 – Prueba

Un paso de prueba opcional envía una notificación a todos tus servicios seleccionados para verificar que todo funciona correctamente.

- Marca **Enviar notificación de prueba ahora** (marcado por defecto) y haz clic en Enviar.
- Desmarca la casilla para omitir este paso.
- Si la prueba falla, se muestra un error. Puedes intentarlo de nuevo o desmarcar la casilla para continuar de todas formas.

### Paso 4 – Avanzado

**Todos los campos son opcionales. El valor 0 desactiva la función correspondiente.**

| Campo | Descripción |
|---|---|
| **Retraso de alerta** | Minutos sin conexión antes de crear un evento. Por defecto: **0** (inmediato). |
| **Tiempo mínimo entre notificaciones** | Tiempo mínimo entre notificaciones inmediatas por dispositivo. Por defecto: **0** (sin límite). |
| **Duración mínima sin conexión** | Eventos más cortos que este valor se excluyen del resumen. Por defecto: **0** (todos los eventos). |
| **Incluir habitación / área** | Mostrar el nombre del área de HA en las notificaciones. Por defecto: **desactivado**. |
| **Incluir fabricante y modelo** | Mostrar información del dispositivo. Por defecto: **desactivado**. |
| **Dominios de entidades excluidos** | Excluye dominios de entidades completos (p. ej. `sensor`, `button`). Las entidades `device_tracker` siempre se excluyen automáticamente. |
| **Entidades excluidas** | Lista de entidades específicas a excluir de la monitorización. |

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

### Configuración inicial recomendada

- **Notificación inmediata:** desactivada
- **Resumen:** activado, diario a las 08:00
- **Retraso de alerta:** 5 minutos (evita falsas alarmas por caídas breves de WiFi)
- **Duración mínima sin conexión:** 5 minutos (mantiene el resumen limpio)
- **Incluir área:** activado (hace las notificaciones mucho más legibles)
- **Umbral HA Repairs:** 24 horas

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

### Resumen

> **Resumen de conexiones**
> 📋 3 dispositivo(s) afectado(s) desde el último resumen:
> • Sensor Cocina [Cocina] (zha): sin conexión desde 05/19 07:15, de nuevo en línea a las 07:42
> • Bombilla Dormitorio [Dormitorio] (hue): sin conexión desde 05/19 09:05 ⚠️ todavía sin conexión
> • Detector Pasillo (esphome): sin conexión desde 05/19 11:20, de nuevo en línea a las 11:28

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

Añádela a la lista *Entidades excluidas* en los ajustes avanzados. Las demás entidades del dispositivo siguen siendo monitorizadas.

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

---

## 13. Limitaciones conocidas

- **Integraciones solo en la nube:** Es posible que los dispositivos conectados exclusivamente a través de un servicio en la nube no se detecten si la integración no establece `unavailable` cuando la nube no está disponible.
- **Integraciones por sondeo:** Una desconexión puede detectarse solo después del siguiente ciclo de sondeo.
- **Cobertura Bluetooth:** Es posible que los dispositivos solo visibles en el nivel del adaptador Bluetooth bruto no estén cubiertos.
- **Una sola instancia:** Connection Observer admite una única instancia de integración por instalación de HA.
- **Retención de eventos 30 días:** Los eventos con más de 30 días se eliminan automáticamente del almacenamiento.
