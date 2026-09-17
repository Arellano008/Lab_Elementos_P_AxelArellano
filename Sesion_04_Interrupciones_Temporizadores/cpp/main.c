#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include "pico/stdlib.h"
#include "pico/time.h"
#include "hardware/gpio.h"

// Juego de los reflejos - Sesion 04 (Interrupciones y Temporizadores)
// Version en C puro (Pico SDK) para el builder de Wokwi.

#define LED_SIGNAL 15
#define LED_WAIT   14
#define BUTTON     16

typedef enum {
    STATE_WAITING = 0,   // esperando la senal, no hay que presionar todavia
    STATE_READY   = 1,   // senal encendida, midiendo tiempo de reaccion
    STATE_DONE    = 2    // ya hay un resultado pendiente de mostrar
} EstadoJuego;

volatile EstadoJuego state = STATE_DONE; // aun no hay ronda activa hasta el primer schedule_round()

volatile uint32_t start_ms     = 0;
volatile uint32_t reaction_ms  = 0;
volatile bool     result_ready = false;
volatile bool     false_start  = false;
volatile uint32_t last_irq_ms  = 0;

uint32_t   round_number = 0;
alarm_id_t timer_id     = 0;

// Callback del temporizador. Se ejecuta en contexto de interrupcion:
// debe ser rapido, sin printf ni sleep.
int64_t show_signal(alarm_id_t id, void *user_data) {
    gpio_put(LED_SIGNAL, 1);
    gpio_put(LED_WAIT, 0);
    start_ms = to_ms_since_boot(get_absolute_time());
    state = STATE_READY;
    return 0; // 0 = no repetir (equivalente a Timer.ONE_SHOT)
}

// ISR del boton.
void button_irq(uint gpio, uint32_t events) {
    if (gpio != BUTTON) return;

    uint32_t now = to_ms_since_boot(get_absolute_time());
    if (now - last_irq_ms < 80) {
        return; // rebote mecanico: ignorar
    }
    last_irq_ms = now;

    if (state == STATE_READY) {
        reaction_ms = now - start_ms;
        gpio_put(LED_SIGNAL, 0);
        result_ready = true;
        state = STATE_DONE;
    } else if (state == STATE_WAITING) {
        cancel_alarm(timer_id);
        false_start = true;
        result_ready = true;
        state = STATE_DONE;
    }
}

void schedule_round(void) {
    round_number++;
    gpio_put(LED_SIGNAL, 0);
    gpio_put(LED_WAIT, 1);
    result_ready = false;
    false_start  = false;
    state = STATE_WAITING;

    uint32_t delay_ms = 1000 + (rand() % 9001); // 1000-10000 ms

    printf("\n================================\n");
    printf("Round %u\n", round_number);
    printf("Espera la senal visual. No presiones antes.\n");
    printf("Delay aleatorio: %u ms\n", delay_ms);
    printf("================================\n");

    timer_id = add_alarm_in_ms(delay_ms, show_signal, NULL, false);
}

int main() {
    stdio_init_all();
    sleep_ms(2000);

    gpio_init(LED_SIGNAL); gpio_set_dir(LED_SIGNAL, GPIO_OUT);
    gpio_init(LED_WAIT);   gpio_set_dir(LED_WAIT, GPIO_OUT);

    gpio_init(BUTTON);
    gpio_set_dir(BUTTON, GPIO_IN);
    gpio_pull_up(BUTTON);

    srand((unsigned int)to_us_since_boot(get_absolute_time()));

    gpio_set_irq_enabled_with_callback(BUTTON, GPIO_IRQ_EDGE_FALL, true, &button_irq);

    printf("JUEGO DE LOS REFLEJOS\n");

    schedule_round();

    while (true) {
        if (result_ready) {
            if (false_start) {
                printf("SALIDA FALSA: presionaste antes de la senal\n");
            } else {
                printf("Reaccion: %u ms\n", reaction_ms);
            }

            sleep_ms(1800);

            while (gpio_get(BUTTON) == 0) { // esperar a que sueltes el boton
                sleep_ms(10);
            }

            schedule_round();
        }
        sleep_ms(20);
    }
}
