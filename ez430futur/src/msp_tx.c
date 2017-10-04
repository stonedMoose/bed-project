/**
 *  \file   main.c
 *  \brief  eZ430-RF2500 tutorial, adc10
 *  \author Antoine Fraboulet, Tanguy Risset, Dominique Tournier
 *  \date   2009
 **/

#include <msp430f2274.h>

#if defined(__GNUC__) && defined(__MSP430__)
/* This is the MSPGCC compiler */
#include <msp430.h>
#include <iomacros.h>
#elif defined(__IAR_SYSTEMS_ICC__)
/* This is the IAR compiler */
//#include <io430.h>
#endif

#include <stdio.h>
#include <limits.h>
#include <string.h>

#include "isr_compat.h"
#include "leds.h"
#include "clock.h"
#include "timer.h"
#include "button.h"
#include "uart.h"
#include "adc10.h"
#include "spi.h"
#include "cc2500.h"
#include "flash.h"
#include "watchdog.h"

#include "pt.h"

#define DBG_PRINTF printf


/* 100 Hz timer A */
#define TIMER_PERIOD_MS 10

#define PKTLEN 3
#define MAX_HOPS 3
#define MSG_BYTE_TYPE 0U
#define MSG_BYTE_HOPS 1U
#define MSG_BYTE_SRC_ROUTE 2U
#define MSG_BYTE_CONTENT (MAX_HOPS + 2)
#define MSG_TYPE_ID_REQUEST 0x00
#define MSG_TYPE_ID_REPLY 0x01
#define MSG_TYPE_TEMPERATURE 0x02

#define NODE_ID_LOCATION INFOD_START

#define NODE_ID_UNDEFINED 0x00
/* 10 seconds to reply to an id request */
#define ID_INPUT_TIMEOUT_SECONDS 3
/* the same in timer ticks */
#define ID_INPUT_TIMEOUT_TICKS (ID_INPUT_TIMEOUT_SECONDS*1000/TIMER_PERIOD_MS)
static unsigned char node_id;

#define NUM_TIMERS 6
static uint16_t timer[NUM_TIMERS];
#define TIMER_LED_RED_ON timer[0]
#define TIMER_LED_GREEN_ON timer[1]
#define TIMER_ANTIBOUNCING timer[2]
#define TIMER_RADIO_SEND timer[3]
#define TIMER_ID_INPUT timer[4]
#define TIMER_RADIO_FORWARD timer[5]


//Variable 

/*
LEDs
*/
static int led_green_duration;
static int led_green_flag;

static int led_red_duration;
static int led_red_flag;

/* Protothread contexts */

#define NUM_PT 3
static struct pt pt[NUM_PT];

/*
 * Radio
 */

static char radio_tx_buffer[PKTLEN];
static char radio_rx_buffer[PKTLEN];
static int radio_rx_flag;
static int periodic_send_flag;

/*
 * UART
 */

static int uart_flag;
static uint8_t uart_data;

static void printhex(char *buffer, unsigned int len)
{
    unsigned int i;
    for(i = 0; i < len; i++)
    {
        printf("%02X ", buffer[i]);
    }
}

static void init_message()
{
    unsigned int i;
    for(i = 0; i < PKTLEN; i++)
    {
        radio_tx_buffer[i] = 0x00;
    }
}

static void radio_send_message()
{
    led_green_on();
    cc2500_utx(radio_tx_buffer, PKTLEN);
    printf("sent: ");
    printhex(radio_tx_buffer, PKTLEN);
    putchar('\r');
    putchar('\n');
    led_green_off();
    cc2500_rx_enter();
}

/* returns 1 if the id was expected and set, 0 otherwise */
static void set_node_id(unsigned char id)
{
    TIMER_ID_INPUT = UINT_MAX;
    if(id!=0){
        if(flash_write_byte((unsigned char *) NODE_ID_LOCATION, id) != 0)
        {
            flash_erase_segment((unsigned int *) NODE_ID_LOCATION);
            flash_write_byte((unsigned char *) NODE_ID_LOCATION, id);
            node_id = id;
            printhex(node_id,1);
            printf("node id set to: %d\n", node_id);
        }
    } 
    else{
        /* retrieve node id from flash */
        node_id = *((char *) NODE_ID_LOCATION);
        printhex(node_id,1);
        printf("node id retrieved from flash: %d\n", node_id);
    }
}

/*
 * Timer
 */

void timer_tick_cb() {
    int i;
    for(i = 0; i < NUM_TIMERS; i++)
    {
        if(timer[i] != UINT_MAX) {
            timer[i]++;
        }
    }
}

int timer_reached(uint16_t timer, uint16_t count) {
    return (timer >= count);
}

/*
 * LEDs
 */

/* asynchronous */
static void led_green_blink(int duration)
{
    led_green_duration = duration;
    led_green_flag = 1;
}

static void led_red_blink(int duration)
{
    led_red_duration = duration;
    led_red_flag = 1;
}

static PT_THREAD(thread_led_green(struct pt *pt))
{
    PT_BEGIN(pt);

    while(1)
    {
        PT_WAIT_UNTIL(pt, led_green_flag);
        led_green_on();
        TIMER_LED_GREEN_ON = 0;
        PT_WAIT_UNTIL(pt, timer_reached(TIMER_LED_GREEN_ON,
          led_green_duration));
        led_green_off();
    }

    PT_END(pt);
}

static PT_THREAD(thread_led_red(struct pt *pt))
{
    PT_BEGIN(pt);
    while(1)
    {
        PT_WAIT_UNTIL(pt, led_red_flag);
        led_red_on();
        TIMER_LED_RED_ON = 0;
        PT_WAIT_UNTIL(pt, timer_reached(TIMER_LED_RED_ON,
          led_red_duration));
        led_red_off();
        TIMER_LED_RED_ON = 0;
        PT_WAIT_UNTIL(pt, timer_reached(TIMER_LED_RED_ON,
          led_red_duration));
    }

    PT_END(pt);
}


/*
 * Radio
 */

static char radio_tx_buffer[PKTLEN];
static char radio_rx_buffer[PKTLEN];
static int radio_rx_flag;

/* to be called from within a protothread */
static void send_temperature()
{
    init_message();
    printf("Node id: %d\n", node_id);

    int temperature = adc10_sample_temp();
    printf("temperature: %d, hex: ", temperature);
    printhex((char *) &temperature, 2);
    putchar('\r');
    putchar('\n');
    /* msp430 is little endian, convert temperature to network order */
    char *pt = (char *) &temperature;
    radio_tx_buffer[0] = node_id;
    radio_tx_buffer[1] = pt[1];
    radio_tx_buffer[2] = pt[0];
    radio_send_message();

}

void radio_cb(uint8_t *buffer, int size, int8_t rssi)
{
    led_green_blink(10); /* 10 timer ticks = 100 ms */
    //DBG_PRINTF("radio_cb :: ");
    switch (size)
    {
        case 0:
            DBG_PRINTF("msg siNode idze 0\r\n");
            break;
        case -EEMPTY:
            DBG_PRINTF("msg emptyr\r\n");
            break;
        case -ERXFLOW:
            DBG_PRINTF("msg rx overflow\r\n");
            break;
        case -ERXBADCRC:
            DBG_PRINTF("msg rx bad CRC\r\n");
            break;
        case -ETXFLOW:
            DBG_PRINTF("msg tx overflow\r\n");
            break;
        default:
            if (size > 0)
            {
                /* register next available buffer in pool */
                /* post event to application */
                //DBG_PRINTF("rssi %d\r\n", rssi);

                //memcpy(radio_rx_buffer, buffer, PKTLEN);
                //FIXME what if radio_rx_flag == 1 already?
                //radio_rx_flag = 1;
            }
            else
            {
                DBG_PRINTF("msg packet error size=%d\r\n",size);
            }
            break;
    }

    cc2500_rx_enter();
}

/*
 * UART
 */


int uart_cb(uint8_t data)
{
    if(data == 27 && uart_flag==0){
        printf("Taper le nouvel id et pressez enter pour accepter\n");
        uart_flag=1;
        periodic_send_flag=0;
    }
    else if(data == 13 && uart_flag==1){
        uart_flag=0;
        periodic_send_flag=1;
    }
    else {
        printf("%c\n",data);
        uart_data = data;       
    }
        
    return 0;
}


static PT_THREAD(thread_uart(struct pt *pt))
{
    PT_BEGIN(pt);

    while(1)
    {
        PT_WAIT_UNTIL(pt, uart_flag==1);
        led_red_on();
        PT_WAIT_UNTIL(pt,uart_flag==0);
        set_node_id(uart_data);
        led_red_off();
    }

    PT_END(pt);
}

static PT_THREAD(thread_periodic_send(struct pt *pt))
{
    PT_BEGIN(pt);

    while(1)
    {
        PT_WAIT_UNTIL(pt,periodic_send_flag==1);
        TIMER_RADIO_SEND = 0;
        PT_WAIT_UNTIL(pt, node_id != NODE_ID_UNDEFINED && timer_reached( TIMER_RADIO_SEND, 100) && periodic_send_flag==1);
        send_temperature();
    }

    PT_END(pt);
}

/*
 * main

 */

int main(int argc, char *argv[])
{
    watchdog_stop();

    TIMER_ID_INPUT = UINT_MAX;
    node_id = NODE_ID_UNDEFINED;

    /* protothreads init */
    int i;
    for(i = 0; i < NUM_PT; i++)
    {
        PT_INIT(&pt[i]);
    }

    /* LEDs init */
    leds_init();
    led_green_flag = 0;
    led_red_flag = 0;

    /* clock init */
    set_mcu_speed_dco_mclk_16MHz_smclk_8MHz();

    /* timer init */
    timerA_init();
    timerA_register_cb(&timer_tick_cb);
    timerA_start_milliseconds(TIMER_PERIOD_MS);

    /* UART init (serial link) */
    uart_init(UART_9600_SMCLK_8MHZ);
    uart_register_cb(uart_cb);
    uart_flag = 0;
    uart_data = 0;

    /* ADC10 init (temperature) */
    adc10_start();

    /* radio init */
    spi_init();
    cc2500_init();
    cc2500_rx_register_buffer(radio_tx_buffer, PKTLEN);
    cc2500_rx_register_cb(radio_cb);
    cc2500_rx_enter();
    radio_rx_flag = 0;
    

    button_enable_interrupt();
    __enable_interrupt();


    //Connection init
    uart_flag = 0;
    periodic_send_flag=1;
    set_node_id(0);

    /* simple cycle scheduling */
    while(1) {
        thread_led_red(&pt[0]);
        thread_uart(&pt[1]);
        thread_periodic_send(&pt[2]);
    }
}
