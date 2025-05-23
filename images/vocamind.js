"use strict"; 

(function() {
    console.log('Sanity Check!');
  })();

//============= global vars in the caged namespace ==========================
var VMind = VMind || {};	  //Define namespace using Object literal notation


VMind.LogLevel = 3; //-- log level: 0-no logs, 1-some logs, 3-very detail logs;
//for log use command: VMind.log( 'This is the console output text', 2 );
//for error use command: VMind.err( 'This is a console error' );

//:--------------------------------------------------------------------------
//: Outputs msg into console log if lvl <= VMind.LogLevel
//:--------------------------------------------------------------------------
VMind.log	= (msg,lvl)=>{lvl<=VMind.LogLevel&&window.console&&console.log(msg);}
VMind.err	= (msg)=>{window.console&&console.error(msg);}
VMind.warn = (msg)=>{window.console&&console.warn(msg);}
  //---------------------------------------------------------------------------
  // Initialize VMind. Kind a constructor
  // Simple function to assign all internal structures and pre-defined params
  //---------------------------------------------------------------------------
  VMind.init = function() {

	VMind.log('Initializing VMind...', 1);

	//-- main Lists for DigiLib
	VMind.calls = [];				  //-- list of dicts/maps for actual calls 
  VMind.call_agents = [];
  VMind.refs = {};          //-- object with text references
	VMind.ishow = [];				  //-- list of item IDs for current presentation after applying a filter
//	VMind.outs = [];					  //-- list of all possible screen layouts
//	VMind.modal = [];				  //-- same as VMind.outs, but for the modal screen
	VMind.hist = [];					  //-- list of layouts to navigate through history
	VMind.h_curr = -1;				  //-- current History index 
	
	//-- support Lists for DigiLib
	VMind.id2indx = new Map();		  //-- dict of item ID -> index in VMind.calls. Warning: ID is int

	//-- Additional common namespaces 
	VMind.item = VMind.call || {};	  //-- object for a call (properties and methods)
	VMind.list = VMind.list || {};	  //-- object for a list of calls (properties and methods)
	VMind.filter = VMind.filter || {};  //-- object for a filter/subset (properties and methods)
  VMind.api = VMind.api || {};	      //-- object for api communication (properties and methods)

	//-- number of visible elements in calls: ==REDO==
	VMind.size = () => VMind.calls.length;

	//-- Supporting vars
	VMind.curr_item = 0;				  //-- current index in VMind.ishow for item navigation
	VMind.curr_list = 0;				  //-- current page for list navigation
	
	//-- DOM element IDs
	VMind.elmID = VMind.elmID || {};	  //-- dict to store DOM element IDs 
  VMind.elmID.inp_upl_file = 'input_upload_file';
	VMind.elmID.modal_main	= 'ModalMain';
	VMind.elmID.modal_box	= 'ModalBox';
	VMind.elmID.modal_head	= 'ModalHeader';
	VMind.elmID.modal_body	= 'ModalBody';

   	//-- namespace for CItem fields
	VMind.fld_id	  = 'id';
	VMind.fld_name = 'iname';
	VMind.fld_type = 'itype';
	VMind.fld_note = 'inote';

	//-- get browser window resolution. See VMind.get_screen_size();
	VMind.width_window = 0; //window.innerWidth; screen.width;
	VMind.height_window = 0; //window.innerHeight; screen.height;
	//-- vars for Modal geometry. See VMind.get_screen_size();
	VMind.width_modalB = 0;	//-- big modal box
	VMind.height_modalB = 0;
	VMind.width_modalS = 0;	//-- small modal box
	VMind.height_modalS = 0;

	VMind.width_mini = 150;	//-- max px width for a mini format

	VMind.url_prefix = '';   //-- add this prefix to all URLs
	VMind.tag_ref = '';		//-- tags reference from table refs.gid
  };//-- function

  VMind.init();		//-- run VMind.init to set all params and namespaces


  //---------------------------------------------------------------------------
  //---------------------------------------------------------------------------
  VMind.out_tab = function( tab_name ){
	VMind.log('VMind.out_tab: '+tab_name, 2);
  	//-- Hide all div with class
  	const collection = document.getElementsByClassName("main_tab");
	  for (let i = 0; i < collection.length; i++) {
  		collection[i].style.display = "none";
	  }//for

	  //-- Show the right tab
	  const elm = document.getElementById(tab_name);
	  if( elm ) {
		  elm.style.display = "block";
	  }//if
  }//-- function VMind.out_tab



  //-------------------------------------------------------------------
  //-------------------------------------------------------------------
  VMind.out_log = function(msg,lvl){
    let res;
	  //-- convert string into object,if needed
    if( VMind.isObject(msg) ) {
        res = msg;
    } else {
        res = {"status":"ok", "msg": msg, "lvl": lvl};
    }//if + else

    if( res.lvl > 1) return false;

    //-- out checking status
    const elm = document.getElementById('activity_log');
    if (elm) {
        const log = document.createElement('div');
        let sHTML = '';
        if( res.status == 'ok' ) {
          sHTML += '<img src="images/success-green-check-mark-icon.png" width="16px" alt="OK" class="log_img"/>&nbsp;';
          //log.className = 'debug_ok';
        } else {
          sHTML += '<img src="images/checkbox-cross-red-icon.png" width="16px" alt="Error" class="log_img"/>&nbsp;';
          //log.className = 'debug_err';
        }//if + else status
        log.innerHTML = sHTML + res.msg; //' - ' +
        elm.insertBefore(log, elm.firstChild);
        //elm.appendChild(log);
    }//if element by ID

    return true;
  }//-- function VMind.out_log


  //-------------------------------------------------------------------
  //-------------------------------------------------------------------
  VMind.out_call_list = function(obj){
    const elm = document.getElementById('call_list');
    if (!elm) {return false;} //-- TBDef: add error reporting
    if( ! VMind.isObject(obj) ) { return false; }

    VMind.log(obj, 2);
    const row = document.createElement('tr');
    let sHTML = '';
    
    const img_no = '<img src="images/checkbox-cross-red-icon.png" width="8px">';
    const img_yes = '<img src="images/success-green-check-mark-icon.png" width="8px">';

    sHTML += '<td class="text">'+obj['created_at']+'</td>';   //Date
    sHTML += '<td class="button" onclick="VMind.api.get_call('+obj['cid']+');">'+obj['call_id']+'</td>';   //Call ID
    sHTML += '<td class="text" >'+(obj['agent_name'] === null ? '&nbsp;':obj['agent_name'])+'</td>';   //Agent
    sHTML += '<td class="text" style="text-align:center">'+VMind.format_seconds(obj['duration'])+'</td>';   //Duration
    sHTML += '<td style="text-align:center">';
    sHTML += (obj['is_transcript']=='Empty'?img_no:img_yes);
    sHTML += '</td>';   //Is Transcript
    sHTML += '<td style="text-align:center">';
    sHTML += (obj['is_analysis']=='Empty'?img_no:img_yes);
    sHTML += '</td>';   //Is Analysis
    sHTML += '<td class="text" style="text-align:center">';
    sHTML += (obj['cust_sentiment'] === null ? '&nbsp;':obj['cust_sentiment'])+'</td>';   //Sentiment
    sHTML += '<td class="text" style="text-align:center">';
    sHTML += (obj['csat_score'] === null ? '&nbsp;':obj['csat_score'])+'</td>';   //CSAT
    sHTML += '<td class="text" style="text-align:center">';
    sHTML += (obj['is_fcr'] === null ? '&nbsp;':(obj['is_fcr']?'Yes':'No'))+'</td>';   //FCR
    sHTML += '<td class="text" style="text-align:center">';
    sHTML += (obj['is_abuse'] === null ? '&nbsp;':(obj['is_abuse']?'<b>Yes</b>':'None'))+'</td>';   //Abuse?
    row.innerHTML = sHTML;
    elm.appendChild(row);
    return true;
  }//-- function VMind.out_call_list


  //-------------------------------------------------------------------
  //-------------------------------------------------------------------
  VMind.out_call = function(obj){
    const elm = document.getElementById('call_details');
    if (!elm) {return false;} //-- TBDef: add error reporting
    if( ! VMind.isObject(obj) ) { return false; }

    VMind.log(obj, 2);
    VMind.setElementHTML('call_id', obj['call_id']); //Call ID

    //-- Agent
    const s_agnt = document.getElementById('l_agents');
    if( s_agnt ){
      s_agnt.setAttribute('onchange', 'VMind.api.update_agent('+obj['cid']+')');
      let sHTML = '<option value="0">&nbsp;</option>';
      VMind.call_agents.forEach( agent => {
        sHTML += '<option value="'+agent['agent_id']+'" ';
        if( agent['agent_id'] == obj['agent_id'] ) sHTML += ' selected ';
        sHTML += '>'+agent['agent_name']+'</option>';
      })// forEach
      s_agnt.innerHTML = sHTML;
    }//if s_agnt
    VMind.setElementHTML( 'created_at', obj['created_at'] ); //Date
    //sHTML += '<div><span class="caption">Duration:</span> <span class="text">';
    //sHTML += VMind.format_seconds(obj['duration'])+'</span></div>';
    VMind.setElementAttribute( 'call_audio', 'src', obj['audio_url'] );
    if( obj['summary'] ) 
    VMind.setElementHTML('call_summary', VMind.wiki2html(obj['summary']) );
    if( obj['transcript'] ) 
      VMind.setElementHTML( 'call_transcript',VMind.out_transcript(obj['transcript']) );
    VMind.setElementHTML( 'cust_sentiment', obj['cust_sentiment'] );
    VMind.setElementHTML( 'cust_satis', obj['csat_score']+'/5' );
    VMind.setElementHTML( 'is_fcr', obj['is_fcr']?'Yes':'No' ); //Justification
    VMind.setElementHTML( 'is_abuse', obj['is_abuse']?'<b>Yes</b>':'None' ); //Justification
    if( VMind.notNull(obj['csat_notes'])) VMind.setElementHTML('csat_notes', VMind.wiki2html(obj['csat_notes']) );
    if( VMind.notNull(obj['fcr_notes'])) VMind.setElementHTML('fcr_notes', VMind.wiki2html(obj['fcr_notes']) );
    if( VMind.notNull(obj['abuse_notes'])) VMind.setElementHTML('abuse_notes', VMind.wiki2html(obj['abuse_notes']) );

    VMind.out_tab('tab_call');
    return true;
  }//-- function VMind.out_call


  //---------------------------------------------------------------------------
  // Update Dashboard DOM elements with object stats
  //---------------------------------------------------------------------------
  VMind.out_dashboard = function(stats){
    let legend = 0, bar=0, bar_width=0;

    //-- Total number of calls
    //const calls_total = stats['calls_total'];
    //VMind.setElementHTML('calls_total',calls_total);

    //===  CSAT score
    const csat_total = stats['csat_stat_5']+stats['csat_stat_4']+stats['csat_stat_3']+stats['csat_stat_2']+stats['csat_stat_1'];
    VMind.setElementHTML(     'csat_total', csat_total);
    
    //-- get bar width in px
    const width_total  = document.getElementById('bar_width_total').offsetWidth;
    const bar_width_max = width_total - 150 - 10;// Legend widht = 150 px

    bar = stats['csat_stat_5'];
    if( bar > 0 ){
        legend = Math.floor( bar / csat_total * 100 );
        bar_width = Math.floor(   bar_width_max * bar / csat_total );
        VMind.log('CSAT 5:bar_width='+bar_width,3);
        VMind.setElementHTML(     'csat_stat_5',legend.toString()+'%');
        VMind.setElementAttribute('csat_stat_5','style','width:'+bar_width.toString()+'px');
    }// if

    bar = stats['csat_stat_4'];
    if( bar > 0 ){
        legend = Math.floor( bar / csat_total * 100 );
        bar_width = Math.floor(   bar_width_max * bar / csat_total );
        VMind.log('CSAT 4:bar_width='+bar_width,3);
        VMind.setElementHTML(     'csat_stat_4',legend.toString()+'%');
        VMind.setElementAttribute('csat_stat_4','style','width:'+bar_width.toString()+'px');
    }// if

    bar = stats['csat_stat_3'];
    if( bar > 0 ){
        legend = Math.floor( bar / csat_total * 100 );
        bar_width = Math.floor(   bar_width_max * bar / csat_total );
        VMind.log('CSAT 3:bar_width='+bar_width,3);
        VMind.setElementHTML(     'csat_stat_3',legend.toString()+'%');
        VMind.setElementAttribute('csat_stat_3','style','width:'+bar_width.toString()+'px');
    }// if

    bar = stats['csat_stat_2'];
    if( bar > 0 ){
        legend = Math.floor( bar / csat_total * 100 );
        bar_width = Math.floor(   bar_width_max * bar / csat_total );
        VMind.log('CSAT 2:bar_width='+bar_width,3);
        VMind.setElementHTML(     'csat_stat_2',legend.toString()+'%');
        VMind.setElementAttribute('csat_stat_2','style','width:'+bar_width.toString()+'px');
    }// if

    bar = stats['csat_stat_1'];
    if( bar > 0 ){
        legend = Math.floor( bar / csat_total * 100 );
        bar_width = Math.floor(   bar_width_max * bar / csat_total );
        VMind.log('CSAT 1:bar_width='+bar_width,3);
        VMind.setElementHTML(     'csat_stat_1',legend.toString()+'%');
        VMind.setElementAttribute('csat_stat_1','style','width:'+bar_width.toString()+'px');
    }// if

    //===== FCR pie 
    const fcr_total = stats['fcr_True']+stats['fcr_False']
    const fcr_true = Math.floor( stats['fcr_True'] / fcr_total * 100 );
    const fcr_false = 100-fcr_true;
    VMind.setElementHTML('fcr_total',fcr_total);

    const elm = document.getElementById('fcr_pie');
    if( elm ){
      VMind.log('FCR True ='+fcr_true+'%',3);
      elm.innerHTML=fcr_true+'%';
      elm.style.setProperty('background', 'conic-gradient(#f1c40f 0 '+fcr_false+'%,#2ecc71 0 '+fcr_true+'%)'); //'
    }// if elm


  }//-- function VMind.out_dashboard


  //---------------------------------------------------------------------------
  //---------------------------------------------------------------------------
  VMind.ref2txt = function(gid,rid){
    if( gid in VMind.refs && rid in VMind.refs[gid]) return VMind.refs[gid][rid]
    else return rid;
  }//-- function VMind.ref2txt


  //-------------------------------------------------------------------
  //-------------------------------------------------------------------
  VMind.div_hide_show = function(elm_id_div, elm_id_img){
    const elm_div = document.getElementById(elm_id_div);
    const elm_img = document.getElementById(elm_id_img);
    if ( ! ( elm_div && elm_img) ) return false;
    if( elm_div.style.display == 'none' ){
      //-- change image
      if( elm_img ) elm_img.src = 'images/arrow-down-3.ico'
      //-- show transcript
      elm_div.style.display = 'block';
    } else {
      //-- change image
      if( elm_img ) elm_img.src = 'images/arrow-right-3.ico'
      //-- hide transcript
      elm_div.style.display = 'none';
    }// if + else
    return true;
  }//-- function VMind.div_hide_show


  //-------------------------------------------------------------------
  //-------------------------------------------------------------------
  VMind.out_transcript = function(arr){
    let sHTML = '';
    arr.forEach( row => {
      sHTML += '<div> - '+row['text']+'</div>'; } );
    return sHTML;
  }//-- function VMind.out_transcript


  //-------------------------------------------------------------------
  // Assumption: msg could be an object or a string
  // If msg is an object, it has structure: 
  // 		{"status":"ok", "msg": "File uploaded", "lvl": 1}
  //-------------------------------------------------------------------
  VMind.out_app_response = function(msg) {
    let res;
	//-- convert string into object,if needed
    if( VMind.isObject(msg) ) {
        res = msg;
        VMind.log(res.status + ': ' + res.msg, res.lvl);
    } else {
        res = {"status":"ok", "msg": msg, "lvl": 1};
        VMind.log(msg);
    }//if + else

    VMind.out_log(res, res.lvl);  //-- Add important messages to the Activity log

    //-- out based on lvl
	  const elm = document.getElementById('upload_log');
    if (elm) {
        if( res.status == 'ok'  && VMind.LogLevel >= res.lvl ) {
            elm.value = '[OK] -' + res.msg+'\n'+ elm.value;
        } else {
            elm.value = '['+res.status+'] - ' + res.msg+'\n'+ elm.value;
        }//if + else status
    }//if + else element by ID
  }// function VMind.out_app_response


  //-------------------------------------------------------------------
  //
  //-------------------------------------------------------------------
  VMind.elm_del_all = function (elm_id) {
    let elm = document.getElementById(elm_id);
    if (elm) {
        while (elm.firstChild) {
            elm.removeChild(elm.firstChild);
        }
    }
  }// function VMind.elm_del_all

  //---------------------------------------------------------------------------
  //---------------------------------------------------------------------------
  VMind.prep_upload_file = function(){
    const fileInput = document.getElementById(VMind.elmID.inp_upl_file);
    const file = fileInput.files[0];

    if (!file) {
        alert('Please choose a file!');
        return false;
    }
    VMind.log('VMind.prep_upload_file: '+file, 2);

    const formData = new FormData();
    formData.append('file', file);

    VMind.api.uploadFile(formData);
	return true;
  }//-- function VMind.prep_upload_file


  //---------------------------------------------------------------------------
  //---------------------------------------------------------------------------
  VMind.ask_bot = function(){
    const user_input = document.getElementById('user_input').value;
    if (!user_input) {
        alert('Please enter a question!');
        return false;
    }// if

    VMind.out_loading_data();
    //-- get selected model
    const model_select = document.getElementById('llm_modes');
    const selected_model = model_select.options[model_select.selectedIndex].value;
    VMind.log('Selected model: '+selected_model, 3);
    VMind.log('VMind.ask_bot: '+user_input, 3);

    const formData = new FormData();
    formData.append('question', user_input);
    formData.append('selected_model', selected_model);

    VMind.api.bot_ask(formData);
    return true;
  }//-- function VMind.ask_bot

  //---------------------------------------------------------------------------
  // Read size of windows into internal vars
  //---------------------------------------------------------------------------
  VMind.get_screen_size = function() {
    if( VMind.width_window != 0 && VMind.height_window != 0 ) return false;
    VMind.width_window = window.innerWidth;
    VMind.height_window = window.innerHeight;
  
    VMind.log('VMind.get_screen_size: width='+VMind.width_window+'; height='+VMind.height_window, 3);
  
    let w,h;
    //-- calculate size for big modal
    w = CInt(VMind.width_window * 0.8);	// 80%
    h = CInt(VMind.height_window * 0.7);	 // 70%
    VMind.width_modalB  = w;	 //-- big modal box
    VMind.height_modalB = h;
  
    //-- calculate size for small modal
    w = CInt(VMind.width_window	* 0.3);	 // 30%
    h = CInt(VMind.height_window * 0.2);	 // 20%
    w = w < 300 ? 300 : w;
    h = h < 200 ? 200 : h;
    VMind.width_modalS  = w;	 //-- small modal box
    VMind.height_modalS = h;
  
    return true;
    }; //--function VMind.get_screen_size
  

  //===========================================================================
  // Wrapper for API calls
  //===========================================================================
  VMind.api.prefix = window.location.protocol +'//' + window.location.host;
  
  //---------------------------------------------------------------------------
  // Get list of available LLM models from the server
  //---------------------------------------------------------------------------
  VMind.api.get_llm_models = async function() {
    VMind.log('VMind.api.get_llm_models', 2);
    try {
        const response = await fetch('/models');
        VMind.api.process_llm_models(response);
    } catch (error) {
        VMind.err('Error:' + error);
        VMind.out_app_response({"status":"error", "msg": error, "lvl": 1});
    }//try + catch
  }//-- function VMind.get_llm_models


  //-------------------------------------------------------------------
  //
  //-------------------------------------------------------------------
  VMind.api.process_llm_models = function(response) {
    if (response.ok) {
        response.json().then(data => { 
          //VMind.log('Bot reply:',3);
          VMind.log(data,3);

          const elm = document.getElementById('llm_modes');
          if (elm) {
            VMind.elm_del_all('llm_modes');
            data.response.llm_models.forEach( obj => {
              const option = document.createElement('option');
              option.value = obj;
              option.text = obj;
              if (obj === data.response.selected_model) {
                option.selected = true; // Select the default model
              }
              elm.appendChild(option);
            });
          }
        });
      } else {
          VMind.err('Error in getting LLM modesl:' + response.statusText);
          VMind.out_app_response({"status":"error","msg":'Error in getting LLM models: ' + response.statusText});
      }// if + else
  }//-- function VMind.api.process_llm_models


  //---------------------------------------------------------------------------
  //---------------------------------------------------------------------------
  VMind.api.check_components = async function() {
    VMind.log('VMind.api.check_components', 2);
    try {
        const response = await fetch('/check_health');
        VMind.api.process_component_status(response);
    } catch (error) {
        VMind.err('Error:' + error);
        VMind.out_app_response({"status":"error", "msg": error, "lvl": 1});
    }//try + catch
  }//-- function VMind.api.check_components


  //-------------------------------------------------------------------
  //-------------------------------------------------------------------
  VMind.api.process_component_status = function(response) {
    if (response.ok) {
        response.json().then(data => { 
          const resp= data.response.logs;
          resp.forEach( obj => VMind.out_log(obj,1) )});
    } else {
          VMind.err('Error in getting status of components:' + response.statusText);
    }// if + else
  }//-- function VMind.api.process_component_status


  //---------------------------------------------------------------------------
  //---------------------------------------------------------------------------
  VMind.api.get_call_list = async function() {
    VMind.log('VMind.api.get_call_list', 2);
    try {
        const response = await fetch('/calls');
        VMind.api.process_call_list(response);
    } catch (error) {
        VMind.err('Error:' + error);
        VMind.out_app_response({"status":"error", "msg": error, "lvl": 1});
    }//try + catch
  }//-- function VMind.api.get_call_list


  //-------------------------------------------------------------------
  //-------------------------------------------------------------------
  VMind.api.process_call_list = function(response) {
    if (response.ok) {
        response.json().then(data => { 
          const resp = data.response['call_list'];
          resp.forEach( obj => VMind.out_call_list(obj) )});
    } else {
          VMind.err('Error in getting list of calls:' + response.statusText);
    }// if + else
  }//-- function VMind.api.process_call_list


  //---------------------------------------------------------------------------
  //---------------------------------------------------------------------------
  VMind.api.get_call = async function(cid) {
    VMind.log('VMind.api.get_call', 2);
    try {
        const response = await fetch('/calls/'+cid);
        VMind.api.process_call_one(response);
    } catch (error) {
        VMind.err('Error:' + error);
        VMind.out_app_response({"status":"error", "msg": error, "lvl": 1});
    }//try + catch
  }//-- function VMind.api.get_call


  //-------------------------------------------------------------------
  //-------------------------------------------------------------------
  VMind.api.process_call_one = function(response) {
    if (response.ok) {
        response.json().then(data => { 
          VMind.out_call( data.response['call'] ) });
    } else {
          VMind.err('Error in getting call details:' + response.statusText);
    }// if + else
  }//-- function VMind.api.process_call_one


  //---------------------------------------------------------------------------
  //---------------------------------------------------------------------------
  VMind.api.uploadFile = async function (formData) {
	  VMind.log('VMind.uploadFile', 2);
    try {
        const response = await fetch('/calls/upload', {
            method: 'POST',
            body: formData
        });
        VMind.api.process_upload_response(response);
    } catch (error) {
        VMind.err('Error:' + error);
		    VMind.out_app_response({"status":"error", "msg": error, "lvl": 1});
    }//try + catch
  }//-- function VMind.api.uploadFile


  //---------------------------------------------------------------------------
  //---------------------------------------------------------------------------
  VMind.api.get_refs = async function(){
    VMind.log('VMind.api.get_refs', 2);
    try {
        const response = await fetch('/refs');
        if (response.ok) {
          response.json().then(data => { 
            VMind.log(data,3);
            VMind.refs = data.response['refs'];});
        } else {
          VMind.err('Error in getting refs:' + response.statusText);
          VMind.out_app_response({"status":"error","msg":'Error in getting list of agents: ' + response.statusText});
        }// if + else

    } catch (error) {
        VMind.err('Error:' + error);
        VMind.out_app_response({"status":"error", "msg": error, "lvl": 1});
    }//try + catch
  }//-- function VMind.api.get_refs



  //---------------------------------------------------------------------------
  //---------------------------------------------------------------------------
  VMind.ref2txt = function(gid,rid){
    if( gid in VMind.refs && rid in VMind.refs[gid]) return VMind.refs[gid][rid]
    else return rid;
  }//-- function VMind.ref2txt


  //---------------------------------------------------------------------------
  //---------------------------------------------------------------------------
  VMind.api.get_agents = async function(){
    VMind.log('VMind.api.get_agents', 2);
    try {
        const response = await fetch('/agents');
        if (response.ok) {
          response.json().then(data => { 
            VMind.log(data,3);
            const resp = data.response['agents'];
            resp.forEach( obj => VMind.call_agents.push(obj) )});
        } else {
          VMind.err('Error in getting agents:' + response.statusText);
          VMind.out_app_response({"status":"error","msg":'Error in getting list of agents: ' + response.statusText});
        }// if + else

    } catch (error) {
        VMind.err('Error:' + error);
        VMind.out_app_response({"status":"error", "msg": error, "lvl": 1});
    }//try + catch
  }//-- function VMind.api.get_agents


  //---------------------------------------------------------------------------
  //---------------------------------------------------------------------------
  VMind.api.bot_ask = async function (formData) {
    VMind.log('VMind.api.bot_ask', 2);
    try {
        const response = await fetch('/bot/ask', {
            method: 'POST',
            body: formData
        });
        VMind.api.process_bot_reply(response);
    } catch (error) {
        VMind.err('Error:' + error);
        VMind.out_app_response({"status":"error", "msg": error, "lvl": 1});
    }//try + catch
  }//-- function VMind.api.bot_ask              


  //-------------------------------------------------------------------
  //
  //-------------------------------------------------------------------
  VMind.api.process_bot_reply = function(response) {
    if (response.ok) {
        response.json().then(data => { 
          VMind.log('Bot reply:',3);
          VMind.log(data,3);

          const elm = document.getElementById('bot_response');

          //-- create child with question
          const question = document.createElement('div');
          question.className = 'user_message';
          const usr_input = document.getElementById('user_input');
          const question_text = usr_input.value;
          question.innerHTML = VMind.wiki2html( question_text );
          usr_input.value = ''; // Clear the input field

          //-- create child with answer
          const answer = document.createElement('div');
          answer.className = 'bot_message';
          answer.innerHTML = VMind.wiki2html( data.response.bot_answer );

          //-- append question and answer to the element
          if (elm) {
            elm.appendChild(question);
            elm.appendChild(answer);
              elm.scrollTop = elm.scrollHeight; // Scroll to the bottom
          } else {
              VMind.err('Error: no element with id=bot_response');
          }//if + else
          VMind.hideModal();
        });
    } else {
        VMind.err('Error in asking bot:' + response.statusText);
        VMind.out_app_response({"status":"error","msg":'Error  in asking bot: ' + response.statusText});
    }// if + else
  }//-- function VMind.api.process_bot_reply



  //-------------------------------------------------------------------
  //
  //-------------------------------------------------------------------
  VMind.api.process_upload_response = function(response) {
    if (response.ok) {
        response.json().then(data => { 
			//VMind.log('File uploaded successfully:',3);
			//VMind.log(data,3);
			VMind.out_app_response({"status":"ok", "msg": "File uploaded successfully", "lvl": 1});
            const resp= data.response.logs;
            resp.forEach( obj => {if(VMind.isObject(obj) ) {VMind.out_app_response(obj);} });
            document.getElementById(VMind.elmID.inp_upl_file).value = ''; // Clear the file input
        });
    } else {
        VMind.err('Error uploading file:' + response.statusText);
        VMind.out_app_response({"status":"error","msg":'Error uploading file: ' + response.statusText});
    }// if + else
  }//-- function VMind.api.process_upload_response


  //-------------------------------------------------------------------
  //-------------------------------------------------------------------
  VMind.api.update_agent = async function(cid){
    const elm = document.getElementById('l_agents');
    if( ! elm ) { 
      VMind.err('VMind.api.update_agent: Could NOT find a DOM element for agent selector');
      return false;
    }
    const agent_id = elm.value;
    VMind.log('VMind.api.update_agent: for call id='+cid+' selected agent_id='+agent_id, 2);
    try {
      const response = await fetch('/calls/'+cid+'/agent/'+agent_id, {
          method: 'POST',
      });
    } catch (error) {
      VMind.err('Error:' + error);
      VMind.out_app_response({"status":"error", "msg": error, "lvl": 1});
    }//try + catch
  }//-- function VMind.api.update_agent


  //---------------------------------------------------------------------------
  //---------------------------------------------------------------------------
  VMind.api.get_dashboard_stats = async function() {
    VMind.log('VMind.api.get_dashboard_stats', 2);
    try {
        const response = await fetch('/stats');
        if (response.ok) {
            response.json().then(data => { 
              const stats = data.response['dashboard_stats'];
              VMind.log(stats,3);
              VMind.out_dashboard(stats)
            });
          
        } else {
          VMind.err('Error in getting dashboard stats:' + response.statusText);
          VMind.out_app_response({"status":"error","msg":'Error in getting dashboard stats: ' + response.statusText});
        }// if + else

    } catch (error) {
        VMind.err('Error:' + error);
        VMind.out_app_response({"status":"error", "msg": error, "lvl": 1});
    }//try + catch
  }//-- function VMind.api.get_dashboard_stats


  //---------------------------------------------------------------------------
  // Make context menu (right click) invisible
  //---------------------------------------------------------------------------
  VMind.hide_ContextMenu = function(){
	  if ( VMind.isContextMenu !== 0 ) {
	    VMind.isContextMenu = 0;
	    VMind.hideElement(VMind.elmID.context_menu);
	  }//if
  }; //-- function VMind.hide_ContextMenu()


  //---------------------------------------------------------------------------
  // onkeyup event 
  //---------------------------------------------------------------------------
  VMind.event_keyup = function(e){
	if ( e.keyCode === 27 ) { //-- the ESC key
		VMind.hideModal();
		VMind.hide_ContextMenu();
	}//if
  }; //-- function VMind.event_keyup


  //---------------------------------------------------------------------------
  // onclick event 
  //---------------------------------------------------------------------------
  VMind.event_click = function(e){
	const button = e.which || e.button;
	if ( button === 1 ) {
		VMind.hide_ContextMenu();
	}//if button
  }; //-- function VMind.event_click


  //---------------------------------------------------------------------------
  // Simple converter/formatter of wiki-style text to HTML. 
  // See https://en.wikipedia.org/wiki/Help:Cheatsheet
  // See https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/replace
  //---------------------------------------------------------------------------
  VMind.wiki2html = function(txt){
    if( VMind.isNull(txt) ) return '';
    txt = txt.replace( /\n/gm, '<br>' );
    txt = txt.replace( /\\n/gm, '<br>' );
    txt = txt.replace( /\*\*(.*?)\*\*/g, '<b>$1</b>' );	//-- bold
    txt = txt.replace( /\/\/(.*?)\/\//g, '<i>$1</i>' );	//-- italic
    txt = txt.replace( /__(.*?)__/g, '<u>$1</u>' );	//-- underline
    return txt;
  };//--function VMind.wiki2html

  //---------------------------------------------------------------------------
  // Resize modal to big size and make it visible
  //---------------------------------------------------------------------------
  VMind.show_modal_big = function(head=null, body=null, width=0, height=0) {
    if( VMind.width_modalB == 0 || VMind.height_modalB == 0 )
      VMind.get_screen_size();
    const elm = document.getElementById(VMind.elmID.modal_box);
    if ( elm )	{
      elm.style.width	 = (width==0?VMind.width_modalB:width) +'px';
      elm.style.height = (height==0?VMind.height_modalB:height) +'px';
      VMind.log( `VMind.showModalBig: resized big modal to 
        ${elm.style.width} x ${elm.style.height}`, 3 );
    }//if
    if( head != null && typeof head == 'string' ) 
      VMind.setElementHTML(VMind.elmID.modal_head, head );
    if( body != null && typeof body == 'string' ) 
      VMind.setElementHTML(VMind.elmID.modal_body, body );
  
    //-- show modal
    VMind.showElement(VMind.elmID.modal_main);
    }; //--function VMind.show_modal_big
  
  
    //---------------------------------------------------------------------------
    // Resize modal to small size and make it visible
    //---------------------------------------------------------------------------
    VMind.show_modal_small = function(head=null, body=null, width=0, height=0) {
    if( VMind.width_modalS == 0 || VMind.height_modalS == 0 )
      VMind.get_screen_size();
    const elm = document.getElementById(VMind.elmID.modal_box);
    if ( elm )	{
      elm.style.width	 = (width==0?VMind.width_modalS:width) +'px';
      elm.style.height = (height==0?VMind.height_modalS:height) +'px';
      VMind.log( `VMind.showModalBig: resized small modal to 
        ${elm.style.width} x ${elm.style.height}`, 3 );
    }//if
    if( head != null && typeof head == 'string' ) 
      VMind.setElementHTML(VMind.elmID.modal_head, head );
    if( body != null && typeof body == 'string' ) 
      VMind.setElementHTML(VMind.elmID.modal_body, body );
  
    //-- show modal
    VMind.showElement(VMind.elmID.modal_main);
    }; //--function VMind.show_modal_small
  
   
  //===================== Support Functions ===================================
  //-- Define some simple support functions in the same namespace
  VMind.isNull = s => s === null;
  VMind.notNull = s => s !== null;
  VMind.isObject = o => o !== null && typeof o == 'object' ;
  VMind.object_size = o => Object.keys(o).length;	//-- returns size/length of object's keys
  VMind.def = s => s !== undefined && s !== null;		//-- true if s defined and not null
  VMind.undef = s => s === undefined;	//-- true if s undefined
  VMind.has = (o,e) => o !== null && typeof o == 'object' && e in o; //-- true if object o has element e
  //-- return Now as epoch
  VMind.epoch = () => { let d = new Date(); return Math.round(d.getTime() / 1000); }
  VMind.epoch2date = e => { e = parseInt(e); if ( isNaN(e) || e <= 0 ) return 'never'; 
	const d = new Date(e * 1000 ); return d.toISOString(); }

  //-- Verifies protocol and returns true if http or https
  VMind.isWeb = () => (location.protocol.match(/^http/i) == null )?false:true;

  let getRandomInt = max => Math.floor(Math.random() * Math.floor(max));

  //---------------------------------------------------------------------------
  // Prepare data to be transfered from browser to the web server as HTTP POST
  // Part of the Client<->Web<->DB encode/decode procedures
  // Input: data as string
  // Output: encoded data
  //---------------------------------------------------------------------------
  VMind.HTMLencode = s => encodeURIComponent( s );
  var CInt = i => parseInt(i);
  let q2 = m => "'"+m+"'";
  let qq2 = m => '"'+m+'"';
  let q2c = m => "'"+m+"',";
  let qq2c = m => '"'+m+'",';


  //---------------------------------------------------------------------------
  // Re-out title and logo
  //---------------------------------------------------------------------------
  VMind.set_title = () => document.title = VMind.title;
  VMind.out_loading_data = () => VMind.show_modal_small('Getting answer...', 
			'<div class="loader"></div>',200,200); //Loading details from the server...
  VMind.getURL = url => VMind.url_prefix.length > 0 && url.match(/^images/i) === null ?  VMind.url_prefix +'/'+url : url;   
  VMind.get_type_name = t => t in VMind.type2name ? (VMind.def( VMind.type2name[t]['txt'] ) ? VMind.type2name[t]['txt'] : t ): t; 
  
  VMind.hideModal = function(){ VMind.hideElement(VMind.elmID.modal_main); };

  //---------------------------------------------------------------------------
  // Return a value from obj[key] if defined or def
  //---------------------------------------------------------------------------
  VMind.setIFdef = function( obj, key, def = undefined ){
	if( obj !== null && typeof obj == 'object' && key in obj ){
		return obj[key];
	} else {
		return def;
	}// if
  }//-- function VMind.setIFdef


//---------------------------------------------------------------------------
  // Make DOM element visible by element ID
  //---------------------------------------------------------------------------
  VMind.showElement = function(elm_id) {
	let elm;
	if(elm_id)	elm = document.getElementById(elm_id);
	if(elm)	 {	 elm.style.display = 'block'; }
	else { VMind.warn( 'VMind.showElement: no DOM element with id='+elm_id ); }
  }//function VMind.showElement


  //---------------------------------------------------------------------------
  // Make DOM element invisible by element ID
  //---------------------------------------------------------------------------
  VMind.hideElement = function(elm_id) {
	let elm;
	if(elm_id)	elm = document.getElementById(elm_id);
	if(elm)	  {	 elm.style.display = 'none'; }
	else { VMind.warn( 'VMind.hideElement: no DOM element with id='+elm_id ); }
  }//function VMind.hideElement


  //---------------------------------------------------------------------------
  // set DOM element value by element ID
  //---------------------------------------------------------------------------
  VMind.setElementValue = function (elm_id,elm_val){
	let elm;
	if(elm_id)	elm = document.getElementById(elm_id);
	if(elm)	  {	 elm.value=elm_val; }
	else { VMind.warn( 'VMind.setElementValue: no DOM element with id='+elm_id ); }
  }//function VMind.setElementValue


  //---------------------------------------------------------------------------
  // set an attribute to a DOM element by element ID
  //---------------------------------------------------------------------------
  VMind.setElementAttribute = function (elm_id,attr,avalue){
	let elm;
	if(elm_id)	elm = document.getElementById(elm_id);
	if(elm)	  {	 elm.setAttribute(attr,avalue); }
	else { VMind.warn( 'VMind.setElementAttribute: no DOM element with id='+elm_id ); }
  }//function VMind.setElementAttribute


  //---------------------------------------------------------------------------
  // Set innherHTML for a DOM element by element ID
  //---------------------------------------------------------------------------
  VMind.setElementHTML = function(elm_id, elm_val) {
	let elm;
	if(elm_id)	elm = document.getElementById(elm_id);
	if(elm) {	 elm.innerHTML=elm_val; }
	else { VMind.warn( 'VMind.setElementHTML: no DOM element with id='+elm_id ); }
  }//function VMind.setElementHTML

  //---------------------------------------------------------------------------
  // Set onClick call back function by a element ID 
  //---------------------------------------------------------------------------
  VMind.set_onclick = function (elm_id, call_back ){
	const elm = document.getElementById(elm_id);
	if( elm ) { elm.onclick=call_back; }
	else { VMind.warn( 'VMind.set_onclick: no DOM element with id='+elm_id ); }
  }; //-- function VMind.set_onclick


  //:--------------------------------------------------------------------------
  // Randomize / shuffle the array
  // Source: https://stackoverflow.com/questions/2450954/how-to-randomize-shuffle-a-javascript-array
  //:--------------------------------------------------------------------------
  VMind.shuffle = function (a) {
	  for (let i = a.length - 1; i > 0; i--) {
		  const j = Math.floor(Math.random() * (i + 1));
		  [a[i], a[j]] = [a[j], a[i]];
	  }//for
	  return a;
  }; //-- function VMind.shuffle


  //:--------------------------------------------------------------------------
  //:--------------------------------------------------------------------------
  VMind.format_seconds = function (seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = seconds % 60;
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(remainingSeconds).padStart(2, '0')}`;
  }; //-- function VMind.format_seconds


  //:--------------------------------------------------------------------------
  //: Create a HTML tag with attributes and more
  //: Input: dict with at least 't':'a_HTML_tag'
  //:	 'attr': to pass tag attributes as a string
  //:	 'b': body of the tag
  //: Output: well-formated HTML or empty string
  //
  //: Input Keys with short version: 
  //:	t or tag - tag like br, div, p, h1, etc
  //:	b or body - tag inner text or HTML
  //:	c or class - tag attribute class
  //   
  //: Example: VMind.tag({t:'div',b:'Hello, World!',c:'caption',id:'div22'});
  //
  //: Updated on Sep 29, 2018 by Eugene Taylashev
  //:--------------------------------------------------------------------------
  VMind.tag = function(a){
	//-- check input arguments
	try {
		if( typeof a != 'object' ) 
			throw('input argument is not an array/map');
		if( a['t'] === undefined && a['tag'] === undefined )
			throw('input map does not have key t: or tag:');
	} catch(err) {
		VMind.warn('VMind.tag: '+err);
		return '';
	}//try + catch

	let sTag = ((a['t'] !== undefined )? a['t'] :
		((a['tag'] !== undefined )?a['tag']:null));	  
	if( sTag === null ) return '';

	if( sTag.toLowerCase() == '&nbsp;' ) return '&nbsp;'; //-- special case, not tag

	const tag_simple = ['br','input', 'img'];
	const int_attr = ['id', 'class', 'style', 'type', 'rel',
		'value', 'name', 'maxlength', 'size', 'src',
		'onclick','ondblclick','oncontextmenu', 'onmouseover', 'onmouseout',
		'onsearch','onkeypress','onkeyup','onload','onchange',
		'alt', 'cols', 'rows', 'href', 'align', 'border', 'title', 'width', 'height'];

	let sHTML = ''; //-- result string
	let sTagBody = ((a['b'] !== undefined )?a['b']:((a['body'] !== undefined )?a['body']:''));
	let sAttr = '';

	sHTML += '<'+sTag;				   //-- open the tag

	//-- do typical attributes
	int_attr.forEach( element => 
		sHTML += (a[element] !== undefined) ? ` ${element}="${a[element]}"`:'' );

	//-- do other attributes
	if( a['c'] !== undefined )	sHTML += ` class="${a['c']}"`;
	if( a['attr'] !== undefined )  sHTML += ' ' + a['attr'];
	
	//-- close and return simple tags
	if( tag_simple.indexOf(sTag) >=0 )
		return sHTML + '>';//'/>'

	sHTML += '>';	//-- close tag for complex HTML			
	sHTML += sTagBody; //-- add tag body
	
	sHTML += '</'+sTag+'>';			 //-- close the tag
	return sHTML;
  };//--function VMind.tag

  
  //:--------------------------------------------------------------------------
  //: Create table as HTML from a list. So, each cell = list value
  //: Input: aHTML - list with well-formatted HTML for <td></td> or 
  //:	 a dict/map with structure {a:cell_attributes,b:cell_body}
  //:	 cols - number of columns
  //:	 rows - number of rows, if null - unlimited
  //:	 aParams - dict with table tag attributes {table:"",tr:"",td:""}
  //:  Output: well-formated HTML as string <table>...</table> 
  //
  //: Updated on Sep 29, 2018 by Eugene Taylashev (imported from php)
  //:--------------------------------------------------------------------------
  VMind.array2table = function ( aHTML, cols=5, rows=5, aParams=[]){
	//-- check input arguments
	try {
		if( typeof aHTML != 'object' ) 
			throw('input argument is not an array/list');
	} catch(err) {
		VMind.warn('VMind.array2table: '+err);
		return '';
	}//try + catch
	
	//-- set default values
	if( aParams == undefined || typeof aParams != 'object' ) aParams=[];
	if( aParams['table'] == undefined ) {aParams['table']='';}
	if(aParams['tr'] == undefined ) {aParams['tr']='';}
	if(aParams['td'] == undefined ) {aParams['td']='';}
	if( cols <= 0 ) cols=1;
	
	//-- start bulding the HTML code
	let sHTML = '<table ' + aParams['table'] + '>';
	let sTblEnd = '</table>';
	let list_len = aHTML.length, c = 0, r = 0, sCellBody, sCellAttr;
	if( cols > 0 && rows <=0 )	{ rows = Math.ceil(list_len/cols);	}
	let max_cell = cols * rows;
	//-- special case: one row, list_len < cols
	if( list_len < cols ) max_cell = list_len;

	for( let i = 0; i < max_cell; ++i ){
//		  VMind.log( '++make_table_from_array: $i='.$i.'; $c='.$c.'; $r='.$r, 2 );
		if( c === 0 ){ sHTML += '<tr '+ aParams['tr']+'>'; }
		//-- analyse payload of aHTML[i]
		//-- it could be string with well-formatted HTML or object {b:'',a:''}
		sCellBody = aHTML[i];
		sCellAttr = aParams['td'];
		if( typeof sCellBody == 'object' ){
		  if( sCellBody['a'] !== undefined) sCellAttr += ' '+sCellBody['a'];
		  sCellBody = sCellBody['b'];
		  }//if sCellBody == 'object'
		sHTML += '<td '+sCellAttr+'>';
		if( i < list_len ){ sHTML += sCellBody; }
		else				{ sHTML += '&nbsp;'; }
		sHTML += '</td>';
		++c;
		if( c >= cols ){ //-- close the row
			sHTML += '</tr>'; 
			c = 0; ++r;
		}//if
		if( r>=rows ){ return sHTML + sTblEnd; }
	}//for

	return sHTML + sTblEnd;
  };//--function VMind.array2table


//================================== END of VMind ==============================

//-- External function: Re-define function init to start after the page loaded
function init(){

//	window.onkeyup = function(e){ VMind.event_keyup(e);} //-- add onkeyup listener
//	document.addEventListener( "click", function(e) { VMind.event_click(e); });
	window.onresize = (e) => { VMind.get_screen_size(); };//window

	//VMind.out_tab('call_list'); //-- !!DEBUG!! 
	document.getElementById('log_level_'+VMind.LogLevel).selected = true;
  VMind.api.check_components(); //-- check if all components are running
  VMind.get_screen_size(); //-- get screen size
  VMind.api.get_llm_models();
  VMind.api.get_agents();
  VMind.api.get_refs();
  VMind.api.get_call_list(); //-- get list of calls
  VMind.api.get_dashboard_stats();
  VMind.out_tab('tab_dashboard')

  }; //--function init()