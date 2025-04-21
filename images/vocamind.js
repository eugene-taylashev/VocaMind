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
  }


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


  //===========================================================================
  // Wrapper for API calls
  //===========================================================================
  VMind.api.prefix = window.location.protocol +'//' + window.location.host;
  
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


  //-------------------------------------------------------------------
  //
  //-------------------------------------------------------------------
  VMind.api.process_upload_response = function(response) {
    if (response.ok) {
        response.json().then(data => { 
			VMind.log('File uploaded successfully:',3);
			VMind.log(data,3);
			VMind.out_app_response({"status":"ok", "msg": "File uploaded successfully", "lvl": 1});
            const resp= data.response;
            resp.forEach( obj => VMind.out_app_response(obj) );
            document.getElementById(VMind.elmID.inp_upl_file).value = ''; // Clear the file input
        });
    } else {
        VMind.err('Error uploading file:' + response.statusText);
        VMind.out_app_response({"status":"error","msg":'Error uploading file: ' + response.statusText});
    }// if + else
  }//-- function VMind.api.process_upload_response


  //---------------------------------------------------------------------------
  // Make context menu (right click) invisible
  //---------------------------------------------------------------------------
  VMind.hide_ContextMenu = function(){
	if ( VMind.isContextMenu !== 0 ) {
	  VMind.isContextMenu = 0;
	  VMind.hideElement(VMind.elmID.context_menu);
	}
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
  VMind.set_logo = () => VMind.setElementHTML( VMind.elmID.logo, VMind.tag({t:'img',src:VMind.img_logo, title:'Logo'}));
  VMind.out_loading_data = () => VMind.show_modal_small('Loading data...', 
			'<div class="loader"></div>',200,200); //Loading details from the server...
  VMind.getURL = url => VMind.url_prefix.length > 0 && url.match(/^images/i) === null ?  VMind.url_prefix +'/'+url : url;   
  VMind.get_type_name = t => t in VMind.type2name ? (VMind.def( VMind.type2name[t]['txt'] ) ? VMind.type2name[t]['txt'] : t ): t; 
  

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
  VMind.format_seconds = function (s) {
	let min = Math.floor( s/60 );
	let r = s;
	r = min > 0 ? min+'m': s;
	return r;
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

	VMind.out_tab('tab_upload'); //-- !!DEBUG!! Show the upload tab onload
	document.getElementById('log_level_'+VMind.LogLevel).selected = true;

  }; //--function init()