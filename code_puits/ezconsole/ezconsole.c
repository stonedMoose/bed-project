/*
 *	ez430 UART communication program.
 *	It is designed to be a userspace replacement of the
 *	buggy cdc_acm kernel driver.
 *
 *	Inspired by python script by Peter A. Bigot under BSD License
 *
 *	Copyright 2013 INRIA
 *	Author : T. Pourcelot, CITI Lab
 */

#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <errno.h>
#include <unistd.h>
#include <strings.h>
#include "error.h"
#include <fcntl.h>
#include <termios.h>
#include <string.h>

#include <pthread.h>

#include "ez430.h"

#ifdef DEBUG 
#define DEBUG_PRINTF(...) fprintf(stderr,__VA_ARGS__)
#else
#define DEBUG_PRINTF(...)
#endif


/*
 * Read bytes from stdin and send them to the device
 */

static void *writer_function(void *arg)
{
	struct ez430_dev *dev = (struct ez430_dev *)arg;
	char buffer;
	int res = 0;

	for (;;) {
	  res = read(STDIN_FILENO, &buffer, 1);
	  //putchar('.');
	  if (buffer == 0x03) {	// exit on C-c
            //putchar('#');
	    break;
	  }
	  if(res == -1)// read error on the terminal
	    {
	      error(1,errno,"error while reading user input");
	    }
	  if (res > 0) {
	    
	    int toto = ez430_write(dev, &buffer, 1);
	    
	    if (toto < 0) {
	      DEBUG_PRINTF("Error %i writing to dev\n",toto);
	    }
	  }
	} //for(;;)
    
	DEBUG_PRINTF("Exiting writer thread!\n");
	pthread_exit(NULL);
}

/*
 * read from the device, print it to stdout
 */
#define BUF_SIZE 50

static void *reader_function(void *arg)
{
	struct ez430_dev *dev = (struct ez430_dev *)arg;
	char buf[BUF_SIZE];
	int r = 0;
	int cancel_state;
	for (;;)
	  {
	    bzero(&buf, BUF_SIZE);
	    
	    /* critical section */
	    /* printf("<"); */
	    pthread_setcancelstate(PTHREAD_CANCEL_DISABLE, &cancel_state);
	    r = ez430_read(dev, &buf, BUF_SIZE-1);
	    pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, &cancel_state);
	    /* printf(">"); */
	    /* end of critical section */
	    
	    if (r > 0) // r is negative on errors (including timeouts)
	      {
		int i;
		for(i=0 ; i<r; i++)
		  {
		    // if( buf[i]== '\n' ) putchar('#'); //help debug newlines (linefeeds)
		    // if( buf[i] == '\r' ) putchar('$'); // help debug carriage-returns
		    
		    putchar(buf[i]);
		    
		    
		    // In interactive mode, we set the terminal was to
		    // raw, so '\n' characters are interpreted as strict
		    // "line-feeds". So we must do the additional
		    // carriage-return ourselves.
		    if(isatty(STDOUT_FILENO) && buf[i] == '\n' ) 
		      putchar('\r');
		  }
		r = 0;
	      }        
	  }
	// dead code
	pthread_exit(NULL);
}

int main(int argc, char **argv)
{
    struct termios oldtio, newtio;
        
	struct ez430_dev *my_dev = NULL;

	pthread_t reader_thread, writer_thread;
    
    // always set standard out to unbuffered mode
    setbuf(stdout, NULL);

	my_dev = ez430_open(my_dev);

	if (my_dev == NULL) {
		error(EXIT_FAILURE, 0, "Failed to open device");
	}
#ifdef DEBUG
	ez430_dump_info(my_dev);
#endif

    // TODO: proper option handling ? (and write a usage() function...)    if(argc < 2 || strcmp(argv[1], "-q"))
        printf("Welcome to ezconsole. Press C-c to exit.\n");

    if(isatty(STDIN_FILENO))
    {
        // disable unwanted terminal features like buffering and local
        // echo (and probably others)
        tcgetattr(STDIN_FILENO, &oldtio);
        cfmakeraw(&newtio);
        tcflush(STDIN_FILENO, TCIFLUSH);
        tcsetattr(STDIN_FILENO, TCSANOW, &newtio);
    }

	pthread_create(&writer_thread, NULL, writer_function, (void *)my_dev);
    pthread_create(&reader_thread, NULL, reader_function, (void *)my_dev);

	pthread_join(writer_thread, NULL);
    DEBUG_PRINTF("main: writer thread joined\n");

    if(isatty(STDIN_FILENO))
    {
        /* restore the original terminal settings */
        tcsetattr(STDIN_FILENO, TCSANOW, &oldtio);
    }
    

    // GS-20/11/2013-20:00 All that cleanup code hangs in many
    // situations (like, when the RF2500 is not plugged to the ez430
    // at all, for instance). It's somehow related to thread
    // synchronization, and the way libusub handles locks and so on.
    //
    // I don't want to spend too much effort on that, and I assume
    // that everything is cleaned up by the kernel when we terminate
    // anyway. So I'm commenting out all that for now, and we'll see
    // if something bad happens.
    
    //DEBUG_PRINTF("main: canceling reader thread\n");
    //pthread_cancel(reader_thread);
    //pthread_join(reader_thread, NULL);
    //DEBUG_PRINTF("All threads have been joined, exiting\n");
    //ez430_close(my_dev);
	return EXIT_SUCCESS;
}
