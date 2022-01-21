// import sqlite3 module
const sqlite3 = require("sqlite3").verbose();
// load modules
const express = require('express');
const app = express();
const {env} = require('process');
const fs = require('fs');
// set the view engine
app.set("view engine", "ejs");
app.set("views", __dirname + "/views");

// set environment variables
let wav_path = env.WAV_PATH || "/data/sound_app/";
let db_name = env.DB_PATH || "/data/sound_app/sound_app.db";
var label_file = env.LABEL_FILE || "/data/sound_app/class_labels.txt";

var table_rows = 0;

// Enable HTML template middleware
app.engine('html', require('ejs').renderFile);

// Enable static CSS styles
app.use(express.static('styles'));

// Enable access to wav files
app.use("/public", express.static(wav_path));

// For processing forms
app.use(express.urlencoded({ extended: true}))

// Read in label file
var labels = [];
try {
  // read file in synchronous way
  // forEach() calls a function for each element in an array
  fs.readFileSync(label_file).toString().split("\n").forEach(function(line, index, arr) {
    if (index === arr.length - 1 && line === "") { return; } // nothing to read anymore
    labels.push(line);
  });
} catch (error) {
  console.log("Error reading label file: ", error); // display runtime error message 
}
console.log("Read in", labels.length, "labels:");
console.log(labels);


function getSQL(filter, srtid) {

  var sql = "SELECT my_rowid, timestamp_created, interpreter_class, interpreter_class_id, interpreter_class2, interpreter_certainty, interpreter_certainty2, current_status, filename, threshold FROM wav_file";

  switch (filter) {
    case "filter1":
      sql = sql + " WHERE current_status = 'evaluated' OR current_status = 'created'"; // All Recordings
      break;
    case "filter2":
      sql = sql + " WHERE current_status = 'deleted'"; // Deleted
      break;
    default:
      sql = sql + " WHERE current_status = 'evaluated' OR current_status = 'created'";
  }
  switch (srtid) {
    case "1":
      sql = sql + " ORDER BY timestamp_created DESC";
      break;
    case "2":
      sql = sql + " ORDER BY current_status";
      break;
    case "3":
      sql = sql + " ORDER BY interpreter_class";
      break;
    default:
      sql = sql + " ORDER BY timestamp_created DESC";
  }
  return sql;
}

// Adding row to entire table
async function buildTable(req) {
  return new Promise( async resolve => {
    let my_table = "";
    let row_html = "";
    // query all rows in database
    db.all(getSQL(req.query.filter, req.query.srtid), [], async (err,rows) => {
      //console.log("buildTable SQL: ", getSQL(req.query.filter, req.query.srtid));
      if (err) {
        return console.error(err.message); // write error message to console
      }
      table_rows = rows.length; // number of files queried
      for (const row of rows) {
        row_html = await buildTableHTML(row); // function execution is paused until Promise is settled
        my_table = my_table + row_html
        //console.log("table row: ", row.filename);
      }  // end for
    resolve(my_table);
    });  // end db
  });  // end promise
}

// Creation of one row
function buildTableHTML(row) {
  return new Promise(resolve => {

    let my_table = "";
    my_table = my_table + "<tr>" +
    "<td style='vertical-align: middle;'><div class='tooltip'>" + row.timestamp_created + "<span class='tooltiptext'>" +  row.filename + "</span></div></td>" +
    "<td style='vertical-align: middle;'>" + row.current_status + "</td><td style='vertical-align: middle;'>"
    if (row.interpreter_class !== null) {
      my_table = my_table + row.interpreter_class;
    } else {
      my_table = my_table + "&nbsp;"; // non breaking space
    }

    if (row.interpreter_certainty !== null) {
        my_table = my_table + " (" + row.interpreter_certainty + "%)";
    }

    my_table = my_table + "</td><td style='vertical-align: middle;'>";
    if (row.interpreter_class2 !== null) {
      my_table = my_table + row.interpreter_class2
    } else {
       my_table = my_table +  "&nbsp;"
    }

    if (row.interpreter_certainty2 !== null) {
      my_table = my_table + " (" + row.interpreter_certainty2 + "%)"
    }

    my_table = my_table + "</td><td style='vertical-align: middle;'>"

    if (row.current_status != "deleted") {
      my_table = my_table + "<audio controls><source src='/public/" + row.filename + "'></audio> &nbsp;" // only can play sound if sound isn't deleted
    }

    my_table = my_table + "</td><td style='vertical-align: middle;'>"

    if (row.current_status != "deleted" || row.current_status == "evaluated") {
      my_table = my_table + "<a class='w3-button w3-circle w3-small w3-red' onclick=\"modalShow('id01'," + row.my_rowid + ", '" + row.filename + "')\"><i class='fa fa-trash'></i></a> &nbsp;&nbsp;"
    }

    my_table = my_table + "</td></tr>"

    resolve(my_table);
    });
}

async function buildExport() {
  return new Promise( async resolve => {
    let my_table = "";
    let row_html = "";
    let sql = "SELECT * FROM wav_file";
    // console.log("start id (outside bracket): ", req.query.startid);
    // if (req.query.startid) {
    //   console.log("start id (inside bracket): ", req.query.startid);
    //   sql = sql + " WHERE my_rowid >= " + req.query.startid; // ??
    // }
    sql = sql + " ORDER BY my_rowid";
    db.all(sql, [], async (err,rows) => {
      console.log("buildExport SQL: ", sql);
      if (err) {
        return console.error(err.message); // write error message to console
      }
      //my_table = `{  "files": [`
      for (const row of rows) {
        row_html = await buildExportJSON(row);
        my_table = my_table + row_html // append each row of data
        my_table = my_table 
        // console.log("table row: ", row.filename);
      }  // end for
      //my_table = my_table + "]  }"
    resolve(my_table);
    });  // end db
  });  // end promise
}

function buildExportJSON(row) {
  return new Promise(resolve => {

    let my_table = "{";
    my_table = my_table + '"my_rowid": "' + row.my_rowid + '",'
    my_table = my_table + '"current_status": "' + row.current_status + '",'
    my_table = my_table + '"timestamp_created": "' + row.timestamp_created + '",'
    my_table = my_table + '"threshold": "' + row.threshold + '",'
    my_table = my_table + '"interpreter_class": "' + row.interpreter_class + '",'
    my_table = my_table + '"interpreter_class2": "' + row.interpreter_class2 + '",'
    my_table = my_table + '"interpreter_certainty": "' + row.interpreter_certainty + '",'
    my_table = my_table + '"interpreter_certainty2": "' + row.interpreter_certainty2 + '",'
    my_table = my_table + '"interpreter_class_id": "' + row.interpreter_class_id + '",'
    my_table = my_table + '"interpreter_class2_id": "' + row.interpreter_class2_id + '",'
    my_table = my_table + '"certainty_threshold": "' + row.certainty_threshold  + '"'

    my_table = my_table + "}"  

    resolve(my_table);
    });
}

//---------
// GET is used to request data from a specified resource
// POST is used to send data to a server to create/update a

// reply to home page request (response)
app.get('/', function (req, res) {
  //getReadyCount(0, cb_readyCount);
  //console.log("GETSQL for home page render: ",  getSQL(req.query.filter, req.query.srtid));

  // req.query: request object populated by request query strings found in URL
  // query strings are in key-value form; start after question mark in URL
  db.all(getSQL(req.query.filter, req.query.srtid), [], (err,rows) => {
    if (err) {
      return console.error(err.message);
    }
  // rendering index.ejs pages
  res.render('index', { model: rows, srtid: req.query.srtid, fil: req.query.filter, frmErr: 'NA', labels: labels, rm: "false"});
  });
});

// reply to table request for AJAX calls (response)
app.get('/table', async function (req, res) {
  let my_table = "";
  //console.log("Get table");
  my_table = await buildTable(req);
  //console.log("my_table: ", my_table);
  //console.log("table moving on...");
  let rr = "      " + table_rows;  // 6 spaces
  res.send(rr.substring(rr.length - 6, rr.length) + my_table); // send number of rows + table contents
});

// reply to export request for JSON export (response)
app.get('/export', async function (req, res) {
  let my_table = "";
  my_table = await buildExport(req);
  res.send(my_table);
});

// post request method requests the server to accept the data enclosed in the body of the request message, most likely for storing it
// update database and webserver after user deletes data at client side
app.post('/', async (req, res) => {
  let frmErr = "NA";

  //console.log('Form submitted: ', req.body);
  let sql = "UPDATE wav_file SET ";

  if (req.body.hidFormName == "id01") {
    // delete file form posted
    // update db
    sql = sql + "timestamp_deleted = datetime('now'), current_status = 'deleted' WHERE (my_rowid = " + req.body.hidWavID1 + ")";
    //console.log("Delete SQL: ", sql);
    db.run(sql, err => {
      if (err) {
        frmErr = err.message;
      }
    });
    // delete file from filesystem containing all WAV files
    fs.unlinkSync(wav_path + req.body.hidWavFile, function (err) {
    if (err) {
      frmErr = frmErr + " " + err.message;
    }
    });
    // check if there were any errors deleting file
    if (frmErr != "NA") {
      frmErr = "<h4 style='color:red;'>Error deleting file: " + frmErr + "</h4>";
    } else {
      frmErr = "<h4 style='color:green;'>File successfully deleted.</h4>";
    }
  } 

  //getReadyCount(0, cb_readyCount);
  //console.log("GETSQL for home page render after POST: ",  getSQL(req.query.filter, req.query.srtid));
  db.all(getSQL(req.query.filter, req.query.srtid), [], (err,rows) => {
    if (err) {
      return console.error(err.message);
    }
  res.render('index', { model: rows, srtid: req.query.srtid, fil: req.query.filter, frmErr: frmErr, labels: labels, rm: "false"});
  });
});

// SQLite database connection
const db = new sqlite3.Database(db_name, err => {
  if (err) {
    return console.error(err.message);
  }
  console.log("Successful connection to the database.");
});

//start a server on port 80 and log its start to our console
var server = app.listen(80, function () {

  var port = server.address().port;
  console.log('Express server listening on port ', port);

});
