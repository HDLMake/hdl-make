quit -sim
make
vsim  -classdebug -uvmcontrol=all -msgmode both -t ps -novopt work.top 
run -all
