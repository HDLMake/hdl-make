/*****************************************************************************
*
* Copyright 2008 Mentor Graphics Corporation
* All Rights Reserved.
*
* THIS WORK CONTAINS TRADE SECRET AND PROPRIETARY INFORMATION WHICH IS THE PROPERTY OF
* MENTOR GRAPHICS CORPORATION OR ITS LICENSORS AND IS SUBJECT TO LICENSE TERMS.
*
*****************************************************************************/

`ifdef MVC_NO_DEPRECATED
// This entire file is deprecated. Testbenches should no longer even include this file.
`__FILE__
`else

`include "uvm_macros.svh"

`define get_interface( _if ) _if
`define DEFINE_VIF_TYPE( IF_NAME ) virtual mgc_``IF_NAME 

`define mvc_report_info( id , mess ) `uvm_info( id , mess , UVM_MEDIUM )
`define mvc_report_warning( id , mess ) `uvm_warning( id , mess )
`define mvc_report_error( id , mess ) `uvm_error( id , mess )
`define mvc_report_fatal( id , mess ) `uvm_fatal( id , mess )

`ifdef MODEL_TECH

`undef m_uvm_get_type_name_func

`define m_uvm_get_type_name_func(T) \
 `uvm_get_type_name_func(T)

`define uvm_get_type_name_func(T) \
  localparam string type_name = `"T`"; \
  virtual function string get_type_name (); \
    return type_name; \
  endfunction

`define mvc_get_type_name_func( specialization ) \
 localparam type_name = specialization; \
 virtual function string get_type_name(); \
   return type_name; \
 endfunction \


//
// The name is a user supplied string unique to this specialization T of a parameterized class
//

`define mvc_object_param_utils( T , name ) \
 `uvm_object_registry(T, name)  \
 `mvc_get_type_name_func( name ) \
 `uvm_field_utils_begin(T) \
 `uvm_object_utils_end

//
// The name is a user supplied string unique to this specialization T of a parameterized class
//

`define mvc_component_param_utils( T , name ) \
 `uvm_component_registry(T, name)  \
 `mvc_get_type_name_func( name ) \
 `uvm_field_utils_begin(T) \
 `uvm_object_utils_end

`else

`define mvc_object_param_utils( T , name ) \
`uvm_object_param_utils( T )

`define mvc_component_param_utils( T , name ) \
`uvm_component_param_utils( T )

`endif 

`endif