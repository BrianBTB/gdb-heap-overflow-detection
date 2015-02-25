# -*- encoding: utf-8 -*-
import gdb
import sys


#needs a source
def getOffset(pattern, length):
    cap_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
    low_letters	= ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
    numbers 	= ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    
    i = 0
    count = 0
    count1 = 0
    count2 = 0
    count3 = 0
    count4 = 0
    
    string = ""
    
    for i in range(0, int(length)):
    	if count == 0:
    		string += cap_letters[count1]
    	
    	elif count == 1:
    		string += low_letters[count2]
    	
    	elif count == 2:
    		string += cap_letters[count3]
    	
    	elif count == 3:
    		string += numbers[count4]
    	
    	count += 1
    
    	if count == 4:
    		count = 0
    
    		count4 += 1
    
    		if count4 == len(numbers):
    			count3 += 1
    			count4 = 0
    
    		if count3 == len(cap_letters):
    			count2 += 1
    			count3 = 0
    
    		if count2 == len(low_letters):
    			count1 += 1
    			count2 = 0
    
    offset = string.find(pattern)
    if offset == -1:
        offset = string.find(pattern.decode('hex')[::-1])
    return offset



wp_list = [];
wp_addr = [];
class ReturnBreak(gdb.FinishBreakpoint):
	_size = 0;	
	def stop(self):
		global wp_list;
		usable_size = gdb.parse_and_eval("malloc_usable_size("+str(self.return_value)+")");
		
		self._size=usable_size
		address = (int(self._size)+int(str(self.return_value),16))
		print "malloc["+str(self._size)+"]="+str(self.return_value)+", adding watchpoint at", hex(address)
		wp_list.append(WatchBreak("*(void**)"+hex(address),gdb.BP_WATCHPOINT,gdb.WP_WRITE,internal=True))
                wp_list[-1]._size = self._size;
		wp_list[-1]._address = self.return_value;
		wp_list[-1]._watch = address;
		#for some reason, returning FALSE causes the next one not to work
		return True

class MallocBreak(gdb.Breakpoint):
	def stop(self):

                val_last_size = gdb.parse_and_eval('bytes');
                bp_t_fin = ReturnBreak(internal = True);
                bp_t_fin.silent=True;
                bp_t_fin._size = val_last_size;
                return False
class FreeBreak(gdb.Breakpoint):
    def stop(self):
        global wp_list
	if gdb.parse_and_eval('mem') == 0x0:
                #suppress free to 0x0, happens internal for some reason
                return False
	tmp_a = [value for value in wp_list if value._address == gdb.parse_and_eval('mem')];
        wp_list.remove(tmp_a[0]);
        #tmp_a[0].remove(); this segfaults. TODO: queue and consumer for breakpoint removal
        return False

class WatchBreak(gdb.Breakpoint):
    _address = 0;
    _size = 0
    _watch = 0;
    def remove(self):
	    print "removing watchpint at",self._watch;
	    #in 7.9, this segfaults (UAF in python engine, admittedly undefined)
            self.delete();
	    return;
    def stop(self):
        #suppress metadata modification internal to libv
	if "malloc" in gdb.execute('where',to_string=True):
	 	return False;
	if "free" in gdb.execute('where',to_string=True):
                return False
	print
	print "overflow detected at: ",gdb.execute("x/i $pc")
	print "offset in overflow buffer: ",getOffset(format(int(gdb.parse_and_eval("*"+str(self._watch))),'x'),300)
	print
	gdb.execute('bt')
	print
	return False;

print 
print "Welcome to CodeLion's heap overflow detection script"
print "You should modify input.py to perform trigger the suspected heap overflow"
print

path = raw_input('Enter path to target executable: ')

gdb.execute('set pagination 0')
gdb.execute('file '+path);
gdb.execute('set can-use-hw-watchpoints 0');

print "GDB can be wierd about malloc and free due to regex matching"
print "Please enter the names for the malloc and free functions"
print "For example, gdb likes to break during program innitialization, which clutters output"
print "to avoid this, don't break directly on 'malloc' and 'free'"
print "you can narrow this down manually, or try one of these:"
print "DLMalloc: malloc.c:malloc, malloc.c:free"
print "GLIBC: __GI___libc_malloc, __GI___libc_free"

print

malloc_name = raw_input("Name of malloc function call [__GI___libc_malloc]: ") or "__GI___libc_malloc"
free_name =   raw_input("Name of free function call [__GI___libc_free]: ") or "__GI___libc_free"
print

bp_malloc = MallocBreak(malloc_name,gdb.BP_BREAKPOINT);
bp_free = FreeBreak(free_name,gdb.BP_BREAKPOINT);
bp_malloc.silent=True;
bp_free.silent = True;


gdb.execute('set debug-file-directory /usr/lib/debug');
gdb.execute('set pagination 0')
gdb.execute('file '+path);
gdb.execute('set can-use-hw-watchpoints 0');


def stopHandler(stopEvent):
    if isinstance(stopEvent,gdb.BreakpointEvent):
            gdb.execute('c')
    return

gdb.events.stop.connect(stopHandler)

gdb.execute('run <<< $(./do_input.py)')

