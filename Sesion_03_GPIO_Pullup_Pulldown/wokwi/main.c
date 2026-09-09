// Semaforo peatonal - Sesion 03 GPIO Pull-up/Pull-down
// Elementos Programables I
//
// Pines (segun la guia de la sesion):
//   Auto rojo     -> GP15
//   Auto amarillo -> GP14
//   Auto verde    -> GP13
//   Peaton rojo   -> GP12
//   Peaton verde  -> GP11
//   Boton         -> GP16 (pull-up interno, presionado = 0)

#include <stdio.h>
#include "pico/stdlib.h"

#define CAR_RED    15
#define CAR_YELLOW 14
#define CAR_GREEN  13
#define PED_RED    12
#define PED_GREEN  11
#define BUTTON     16

// Un solo lugar que decide que LEDs se prenden -> evita estados peligrosos por accidente
void set_lights(bool car_r, bool car_y, bool car_g, bool ped_r, bool ped_g) {
    gpio_put(CAR_RED,    car_r);
    gpio_put(CAR_YELLOW, car_y);
    gpio_put(CAR_GREEN,  car_g);
    gpio_put(PED_RED,    ped_r);
    gpio_put(PED_GREEN,  ped_g);
}

// S0 - REPOSO: autos pasan, peaton espera
void cars_go() {
    set_lights(0, 0, 1,   1, 0);
}

// S1 - TRANSICION: autos se preparan a frenar
void cars_prepare_to_stop() {
    set_lights(0, 1, 0,   1, 0);
}

// S2 - CRUCE: peaton cruza
void pedestrians_go() {
    set_lights(1, 0, 0,   0, 1);
}

// Secuencia completa que se dispara al presionar el boton
void crossing_sequence() {
    printf("S1 TRANSICION: autos amarillo, peaton rojo\n");
    cars_prepare_to_stop();
    sleep_ms(1500);

    printf("S2 CRUCE: autos rojo, peaton verde\n");
    pedestrians_go();
    sleep_ms(4000);

    printf("S3 FIN: peaton verde parpadea\n");
    for (int i = 0; i < 4; i++) {
        gpio_put(PED_GREEN, !gpio_get(PED_GREEN));
        sleep_ms(300);
    }

    printf("S0 REPOSO: autos verde, peaton rojo\n");
    cars_go();
}

int main() {
    stdio_init_all();
    sleep_ms(2000); // da tiempo a abrir el monitor serial antes de imprimir

    // Salidas del semaforo
    gpio_init(CAR_RED);    gpio_set_dir(CAR_RED, GPIO_OUT);
    gpio_init(CAR_YELLOW); gpio_set_dir(CAR_YELLOW, GPIO_OUT);
    gpio_init(CAR_GREEN);  gpio_set_dir(CAR_GREEN, GPIO_OUT);
    gpio_init(PED_RED);    gpio_set_dir(PED_RED, GPIO_OUT);
    gpio_init(PED_GREEN);  gpio_set_dir(PED_GREEN, GPIO_OUT);

    // Entrada del boton con pull-up interno (libre = 1, presionado = 0)
    gpio_init(BUTTON);
    gpio_set_dir(BUTTON, GPIO_IN);
    gpio_pull_up(BUTTON);

    // Estado inicial: S0 REPOSO
    cars_go();
    printf("Sistema listo. S0 REPOSO: autos verde / peaton rojo\n");

    while (true) {
        if (gpio_get(BUTTON) == 0) {
            // Posible click -> debounce: esperar 30ms y confirmar
            sleep_ms(30);
            if (gpio_get(BUTTON) == 0) {
                printf("CLICK valido: peaton solicito cruce\n");
                crossing_sequence();

                // Wait for release: no repetir la secuencia mientras siga presionado
                while (gpio_get(BUTTON) == 0) {
                    sleep_ms(10);
                }
            }
        }
        sleep_ms(10);
    }
}