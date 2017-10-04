
CFLAGS = -g -O0 -Wall
#CFLAGS += -DDEBUG=DEBUG

ifdef DEBUG
	CFLAGS += -DDEBUG=$(DEBUG)
endif

ezconsole: ezconsole.o ez430.o
		gcc -static -pthread -o $@ $^ `pkg-config --libs --cflags libusb-1.0` 
#      Patch found on http://stackoverflow.com/questions/7741141/compiling-against-libusb-dev-on-ubuntu
#      to compile statically ezconsole
#	gcc -static -pthread -o $@ $^ -lusb-1.0 -lrt 
# note: on -pthread VS -lpthread, see http://stackoverflow.com/q/2348200/

%.o: %.c
	gcc -o $@ $(CFLAGS) -c $^

clean: 
	-rm -f *.o ezconsole

