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
#include "uart.h"
#include "adc10.h"
#include "watchdog.h"

#include "spi.h"
#include "cc2500.h"
#include "flash.h"

#include "pt.h"

#define DBG_PRINTF printf


/* 100 Hz timer A */
#define TIMER_PERIOD_MS 10

#define PKTLEN 7

#define NUM_TIMERS 3
static uint16_t timer[NUM_TIMERS];
#define TIMER_LED_GREEN_ON timer[0]  //handle duration of green ligth signal
#define TIMER_UART timer[1]         // handle duration of sampling and sending of  temperature which triggers green light
#define TIMER_RX timer[2]  

#define DELAY_LED_GREEN  10    //delay of 100 ~ 1 seconde for red blinking
#define DELAY_UART 100

/*
 * Timer
 */

/* timer interrupt handler: increases timer's counter */
/* approximately every 10ms                           */ 
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

static void printhex(char *buffer, unsigned int len)
{
    unsigned int i;
    for(i = 0; i < len; i++)
    {
        printf("%02X ", buffer[i]);
    }
    printf("\n");
}

static int converter(char a, char b){
    char s[4];
    sprintf(s,"%02X%02X \n",a,b);
    int number[4]; 
    int i;
    for(i=0;i<4;i++){
        switch(s[i]){
            case '0':
                number[3-i]=0;break;
            case '1':
                number[3-i]=1;break;
            case '2':
                number[3-i]=2;break;
            case '3':
                number[3-i]=3;break;
            case '4':
                number[3-i]=4;break;
            case '5':
                number[3-i]=5;break;
            case '6':
                number[3-i]=6;break;
            case '7':
                number[3-i]=7;break;
            case '8':
                number[3-i]=8;break;
            case '9':
                number[3-i]=9;break;
            case 'A':
                number[3-i]=10;break;
            case 'B':
                number[3-i]=11;break;
            case 'C':
                number[3-i]=12;break;
            case 'D':
                number[3-i]=13;break;
            case 'E':        
                number[3-i]=14;break;
            case 'F':        
                number[3-i]=15;break;
        }
    }
    return number[0]+number[1]*16+number[2]*16*16+number[3]*16*16*16;
    
}



/*
 * LEDs
 */

static int led_green_flag;

static PT_THREAD(thread_led_green(struct pt *pt))
{
    PT_BEGIN(pt);

    led_green_flag=0;
    
    while(1)
      {
        PT_WAIT_UNTIL(pt, led_green_flag);
        led_green_on();
        TIMER_LED_GREEN_ON = 0;
        PT_WAIT_UNTIL(pt, timer_reached(TIMER_LED_GREEN_ON, DELAY_LED_GREEN));
        led_green_off();
	    led_green_flag=0;	
    }

    PT_END(pt);
}


/*
 * UART
 */


static PT_THREAD(thread_uart(struct pt *pt))
{
    PT_BEGIN(pt);

    while(1)
    {

	TIMER_UART=0;
	PT_WAIT_UNTIL(pt, timer_reached(TIMER_UART, DELAY_UART));
	led_green_flag=1;
	int temperature = adc10_sample_temp();
    printf("{\"id\" : \"20\", \"temperature\" : \"%d,%d\"}\n\r",temperature/10,temperature%10);
    }
    
    PT_END(pt);
}

/* RX */

static char radio_tx_buffer[PKTLEN];
static char radio_rx_buffer[PKTLEN];
static int radio_rx_flag;

void radio_cb(uint8_t *buffer, int size, int8_t rssi)
{
        if (size > 0)
        {
            memcpy(radio_rx_buffer, buffer, PKTLEN);
            radio_rx_flag = 1;
        }
        else
        {
            //DBG_PRINTF("msg packet error size=%d\r\n",size);
            //J'ai commenté la ligne supérieure pour la démo
        }

    cc2500_rx_enter();
}


static PT_THREAD(thread_rx(struct pt *pt))
{
    PT_BEGIN(pt);

    while(1)
    {
        PT_WAIT_UNTIL(pt, radio_rx_flag == 1);
        ezdisplay(radio_rx_buffer);
        radio_rx_flag = 0;
    }

    PT_END(pt);
}

void ezdisplay(char message[])
{
    char mspid=message[0];
    char msptemperature1=message[1];
    char msptemperature2=message[2];
    int temperature=converter(msptemperature1, msptemperature2);
    int room=0;
    if (mspid>=49 && mspid<=57){room=1;}
    else if(mspid>=65 && mspid<=90){room=2;mspid-=16;}
    else if(mspid>=97 && mspid<=122){room=2;;mspid-=48;}
    if(room!=0){
        printf("{\"id\" : \"%d%c\", \"temperature\" : \"%d,%d\"}\n\r", room, mspid, temperature/10, temperature%10);
    }
}


/*
 * main
 */
/* Protothread contexts */

#define NUM_PT 3
static struct pt pt[NUM_PT];

int main(void)
{
    watchdog_stop();

    /* protothreads init */
    int i;
    for(i = 0; i < NUM_PT; i++)
    {
        PT_INIT(&pt[i]);
    }

    /* clock init */
    set_mcu_speed_dco_mclk_16MHz_smclk_8MHz();

    /* LEDs init */
    leds_init();
    led_red_off();
    led_green_off();

    /* timer init */
    timerA_init();
    timerA_register_cb(&timer_tick_cb);
    timerA_start_milliseconds(TIMER_PERIOD_MS);

    /* UART init (serial link) */
    uart_init(UART_9600_SMCLK_8MHZ);

    /* ADC10 init (temperature) */
    adc10_start();

    /* radio init */
    
    spi_init();
    cc2500_init();
    cc2500_rx_register_buffer(radio_tx_buffer, PKTLEN);
    cc2500_rx_register_cb(radio_cb);
    cc2500_rx_enter();
    radio_rx_flag = 0;
    
    __enable_interrupt();


    /* simple cycle scheduling */
    while(1) {
      thread_led_green(&pt[0]);
      thread_uart(&pt[1]);
      thread_rx(&pt[2]);
    }
}
