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
#define TIMER_SEND 1050
#define TIMER_SENSING_TEMP 100 //10timer tick = 100ms so here its 100timer tick so 1sec

#define PKTLEN 28


#define NODE_ID_LOCATION INFOD_START
#define NODE_ID_UNDEFINED 0x0000
static unsigned int node_id;


#define NUM_TIMERS 7
static uint16_t timer[NUM_TIMERS];
#define TIMER_LED_RED_ON timer[0]
#define TIMER_LED_GREEN_ON timer[1]
#define TIMER_ID_INPUT timer[2]
#define TIMER_UART timer[3]         // handle duration of sending of  temperature which triggers green light
#define TIMER_RX timer[4]  
#define TIMER_TEMP timer[5]
#define TIMER_WRITE timer[6]


#define DELAY_LED_GREEN  10    //delay of 100 ~ 1 seconde for red blinking
#define DELAY_UART 100


//Variable 

/*
LEDs
*/
static int led_green_duration;
static int led_green_flag;

static int led_red_duration;
static int led_red_flag;

/*
 * Radio
 */


static int periodic_write_flag;
static int periodic_temp_flag;
static int current_buffer_pt;

/*
 * UART
 */

static int uart_flag;
static uint16_t uart_data;
static int room_flag;
static uint8_t room;

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

/* returns 1 if the id was expected and set, 0 otherwise */
static void set_node_id(unsigned int id)
{
    TIMER_ID_INPUT = UINT_MAX;
    if(id!=0){
        if(flash_write_byte((unsigned char *) NODE_ID_LOCATION, id) != 0)
        {
            flash_erase_segment((unsigned int *) NODE_ID_LOCATION);
            flash_write_word((unsigned int *) NODE_ID_LOCATION, id);
            node_id = id;
            printf("node id set to: %x\n", node_id);
        }
    } 
    else{
        /* retrieve node id from flash */
        node_id = *((unsigned int *) NODE_ID_LOCATION);
        printf("node id retrieved from flash:  %x\n", node_id);
    }
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
 * UART
 */

int uart_cb(uint8_t data)
{
    
    if(data == 27 && uart_flag==0){ //27 is ESC ascii code (decimal) 
        printf("Enter new id starting with the room number and then the sensor number. Press enter to accept\n");
        room_flag = 0;
        uart_data = 0;
        uart_flag=1;
        periodic_write_flag=0;
        periodic_temp_flag=0;
    }
    else if(data == 13 && uart_flag==1){ //13 is return/enter ascii code
        uart_flag=0;
        periodic_write_flag=1;
        periodic_temp_flag=1;
    }
    else {
    	if(room_flag == 0){
    		printf("room : %c (hex code : %x)\n",data, data);
    		room = data;
    		room_flag=1;
    		
    	}
        else if (room_flag == 1){
        	printf("sensor: %c (hex code : %x)\n",data,data);
        	uart_data = ((room & 0xFF) <<8) | (data & 0xFF) ;
        	//printf("uart_data : %x \n",uart_data);
        	room_flag = 0;
        }      
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

/* RX */

static char radio_tx_buffer[PKTLEN]; //used as temperature buffer
static char radio_rx_buffer[PKTLEN];
static int radio_rx_flag;

void radio_cb(uint8_t *buffer, int size, int8_t rssi)
{
        if (size > 0)
        {
            memcpy(radio_rx_buffer, buffer, PKTLEN);
            printhex(radio_rx_buffer,PKTLEN);
            radio_rx_flag = 1;
        }
        else
        {
            //DBG_PRINTF("msg packet error size=%d\r\n",size);
            //J'ai commenté la ligne supérieure pour la démo
        }

    cc2500_rx_enter();
}

void ezdisplay(char message[])
{
    char msproom=message[0]&0xFF;
    char mspsensor=message[1]&0xFF;
    int time=0;
    printf("{\"id\" : \"%c%c\"\n",msproom,mspsensor);
    int i=3; //index 2 is the space charactere
    while( i < PKTLEN-1)
    {
    	char msptemperature1=message[i++];
   	char msptemperature2=message[i++];
   	if ((message[i-1]&0xFF) == 0x2E || (message[i-2]&0xFF) == 0x2E )
   	{
   		break;
   	}
    	int temperature=converter(msptemperature1, msptemperature2);
    	time += TIMER_SENSING_TEMP;
    	printf("\"temperature\" : \"%d,%d\", \"time\" : \"+%d\"}\n\r",temperature/10, temperature%10, time);
    }
}

static PT_THREAD(thread_rx(struct pt *pt))
{
    PT_BEGIN(pt);

    while(1)
    {
        PT_WAIT_UNTIL(pt, radio_rx_flag == 1);
        led_green_on();
        ezdisplay(radio_rx_buffer);
        radio_rx_flag = 0;
        led_green_off();
    }

    PT_END(pt);
}




static void init_message()
{
    unsigned int i;
    for(i = 0; i < PKTLEN; i++)
    {
        radio_tx_buffer[i] = 0x00;
    }
    radio_tx_buffer[0] = (node_id>>8) &0xFF;
    radio_tx_buffer[1] = node_id & 0xFF;
    radio_tx_buffer[2] = 0x20;//hex code for SPACE char
    current_buffer_pt = 3;
}


static void write_message()
{
    //finish the sending buffer with a dot 
    radio_tx_buffer[current_buffer_pt] = 0x2E; //dot hex code
    current_buffer_pt = 0;
    led_green_on();
    ezdisplay(radio_tx_buffer);
    led_green_off();
   
}



static PT_THREAD(thread_periodic_writeTemp(struct pt *pt))
{
    PT_BEGIN(pt);

    while(1)
    {
        PT_WAIT_UNTIL(pt,periodic_write_flag==1);
        TIMER_WRITE = 0;
        init_message();
        PT_WAIT_UNTIL(pt, node_id != NODE_ID_UNDEFINED && timer_reached( TIMER_WRITE, TIMER_SEND) && periodic_write_flag==1);
        write_message();
    }

    PT_END(pt);
}


/*
 * TEMP SENSOR
 */
 
 /* to be called from within a protothread */
static void register_temperature()
{
    
    int temperature = adc10_sample_temp();
    /* msp430 is little endian, convert temperature to network order */
    char *pt = (char *) &temperature;    
    radio_tx_buffer[current_buffer_pt++] = pt[1];
    radio_tx_buffer[current_buffer_pt++] = pt[0];
    
}

static PT_THREAD(thread_periodic_temperature(struct pt *pt))
{
    PT_BEGIN(pt);

    while(1)
    {
        PT_WAIT_UNTIL(pt,periodic_temp_flag==1);
        TIMER_TEMP = 0;
        PT_WAIT_UNTIL(pt, node_id != NODE_ID_UNDEFINED && timer_reached( TIMER_TEMP, TIMER_SENSING_TEMP) && periodic_temp_flag==1);
        register_temperature();
    }

    PT_END(pt);
}
/*
 * main
 */
/* Protothread contexts */

#define NUM_PT 5
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
    led_green_flag = 0;
    led_red_flag = 0;

    /* timer init */
    timerA_init();
    timerA_register_cb(&timer_tick_cb);
    timerA_start_milliseconds(TIMER_PERIOD_MS);

    /* UART init (serial link) */
    uart_init(UART_9600_SMCLK_8MHZ);
    uart_register_cb(uart_cb);
    uart_flag = 0;
    uart_data = 0x0000;
    room = 0;
    room_flag = 0;

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


    //Connection init
    uart_flag = 0;
    periodic_write_flag=1;
    periodic_temp_flag=1;
    set_node_id(0);

    /* simple cycle scheduling */
    while(1) {
      thread_led_red(&pt[0]);
      thread_uart(&pt[1]);//for setting node ID
      thread_rx(&pt[2]); //for writing on ezconsole reception temp
      thread_periodic_temperature(&pt[3]);//for sampling temp
      thread_periodic_writeTemp(&pt[4]);//for writing own temp on ezconsole
    }
}
