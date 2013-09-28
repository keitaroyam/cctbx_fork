# -*- mode: python; coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-
#
# $Id$

from __future__ import division

from cctbx.array_family import flex


def _execute(db_commands_queue, db_results_queue, db, semaphore):
  """The _execute() function defines a consumer process that executes
  commands on the SQL database in serial.
  """

  # Acquire the semaphore when the consumer process is starting, and
  # release it on return.
  semaphore.acquire()

  # Process commands from the commands queue and mark them as done.
  cursor = db.cursor()
  while True:
    command = db_commands_queue.get()
    if command is None:
      break

    parameters = command[1]
    if len(parameters) > 1:
      cursor.executemany(command[0], parameters)
    else:
      cursor.execute(command[0], parameters[0])
      lastrowid_key = command[2]
      if lastrowid_key is not None:
        db_results_queue.put((lastrowid_key, cursor.lastrowid))
    db_commands_queue.task_done()

  # Mark the terminating None command as done.
  db_commands_queue.task_done()

  # Commit all the processed commands and join the commands queue.
  db.commit()
  db_commands_queue.join()
  semaphore.release()


class manager:
  # The manager

  def __init__(self, params):
    import multiprocessing
    import sqlite3

    self.params = params

    mgr = multiprocessing.Manager()
    self._db_commands_queue = mgr.JoinableQueue()
    self._db_results_queue = mgr.JoinableQueue()
    self._semaphore = mgr.Semaphore()

    self._db = sqlite3.connect('%s.sqlite' % self.params.runtag)
    multiprocessing.Process(
        target=_execute,
        args=(self._db_commands_queue,
              self._db_results_queue,
              self._db,
              self._semaphore)).start()


  def initialize_db(self, indices):
    cursor = self._db.cursor()
    for table in self.merging_schema_tables(self.params.runtag):
      cursor.execute("DROP TABLE IF EXISTS %s;"%table[0])
      cursor.execute("CREATE TABLE %s " %
                     table[0] + table[1].replace("\n", " ") + " ;")

    # Beware of SQL injection vulnerability (here and elsewhere).
    cursor.executemany("INSERT INTO %s_miller VALUES (NULL, ?, ?, ?)" %
                       self.params.runtag, indices)

    self._db.commit()


  def _insert(self, table, **kwargs):
    """The _insert() function generates the SQL command and parameter
    argument for the _execute() function.
    """

    sql = ("INSERT INTO %s (" % table) \
          + ", ".join(kwargs.keys()) + ") VALUES (" \
          + ", ".join(["?"] * len(kwargs.keys())) + ")"

    # If there are more than one rows to insert, "unpack" the keyword
    # argument iterables and zip them up.  This effectively rearranges
    # a list of columns into a list of rows.
    try:
      parameters = zip(*kwargs.values())
    except TypeError:
      parameters = [kwargs.values()]

    return (sql, parameters)


  def insert_frame(self, **kwargs):
    # Explicitly add the auto-increment column for SQLite.
    (sql, parameters) = self._insert(
        table='%s_frame' % self.params.runtag,
        frame_id_1_base=None,
        **kwargs)

    # Pick up the index of the row just added.  The file name is
    # assumed to to serve as a unique key.
    lastrowid_key = kwargs['unique_file_name']
    self._db_commands_queue.put((sql, parameters, lastrowid_key))
    while True:
      item = self._db_results_queue.get()
      self._db_results_queue.task_done()
      if item[0] == kwargs['unique_file_name']:
        # Entry in the observation table is zero-based.
        return item[1] - 1
      else:
        # If the key does not match, put it back in the queue for
        # someone else to pick up.
        self._db_results_queue.put(item)


  def insert_observation(self, **kwargs):
    (sql, parameters) = self._insert(
        table='%s_observation' % self.params.runtag,
        **kwargs)

    self._db_commands_queue.put((sql, parameters, None))


  def join(self):
    """The join() function closes the database.
    """

    # Terminate the consumer process by feeding it a None command and
    # wait for it to finish.
    self._db_commands_queue.put(None)
    self._db_commands_queue.join()
    self._db_results_queue.join()
    self._semaphore.acquire()

    self._db.close()


  def read_indices(self):
    from cctbx.array_family import flex

    cursor = self._db.cursor()
    millers = dict(merged_asu_hkl=flex.miller_index())
    cursor.execute("SELECT h,k,l FROM %s_miller ORDER BY hkl_id_1_base"%self.params.runtag)
    for item in cursor.fetchall():
      millers["merged_asu_hkl"].append((item[0],item[1],item[2]))
    return millers


  def read_observations(self):
    cursor = self._db.cursor()
    cursor.execute("SELECT hkl_id_0_base,i,sigi,frame_id_0_base,original_h,original_k,original_l FROM %s_observation" % self.params.runtag)
    ALL = cursor.fetchall()

    return dict(hkl_id = flex.int([a[0] for a in ALL]), #as MySQL indices are 1-based
               i = flex.double([a[1] for a in ALL]),
               sigi = flex.double([a[2] for a in ALL]),
               frame_id = flex.int([a[3] for a in ALL]),
               original_h = flex.int([a[4] for a in ALL]),
               original_k = flex.int([a[5] for a in ALL]),
               original_l = flex.int([a[6] for a in ALL]),
               )

  def read_frames(self):
    from xfel.cxi.util import is_odd_numbered

    cursor = self._db.cursor()
    cursor.execute("""SELECT
    frame_id_1_base,wavelength,c_c,slope,offset,res_ori_1,res_ori_2,res_ori_3,
    res_ori_4,res_ori_5,res_ori_6,res_ori_7,res_ori_8,res_ori_9,
    unique_file_name
    FROM %s_frame"""%self.params.runtag)
    ALL = cursor.fetchall()
    from cctbx.crystal_orientation import crystal_orientation
    orientations = [crystal_orientation(
     (a[5],a[6],a[7],a[8],a[9],a[10],a[11],a[12],a[13]),False) for a in ALL]
    return dict( frame_id = flex.int( [a[0]-1 for a in ALL] ),
               wavelength = flex.double( [a[1] for a in ALL] ),
                       cc = flex.double( [a[2] for a in ALL] ),
                    slope = flex.double( [a[3] for a in ALL] ),
                   offset = flex.double( [a[4] for a in ALL] ),
             odd_numbered = flex.bool( [is_odd_numbered(a[14]) for a in ALL] ),
              orientation = orientations,
                unit_cell = [CO.unit_cell() for CO in orientations] )

  def merging_schema_tables(self,runtag):

    # http://www.sqlite.org/faq.html#q1
    return [(runtag+"_observation","""
            (
              hkl_id_0_base INTEGER,
              i DOUBLE(14,8) NOT NULL,
              sigi DOUBLE(14,8) NOT NULL,
              detector_x DOUBLE(8,2) NOT NULL,
              detector_y DOUBLE(8,2) NOT NULL,
              frame_id_0_base INTEGER,
              overload_flag INTEGER,
              original_h INTEGER NOT NULL,
              original_k INTEGER NOT NULL,
              original_l INTEGER NOT NULL
            )
            """),
            (runtag+"_frame","""
            (
              frame_id_1_base INTEGER PRIMARY KEY,
              wavelength DOUBLE(14,8) NOT NULL,
              beam_x DOUBLE(14,8) NOT NULL,
              beam_y DOUBLE(14,8) NOT NULL,
              distance DOUBLE(14,8) NOT NULL,
              c_c DOUBLE(10,7) NOT NULL,
              slope DOUBLE(11,8) NOT NULL,
              offset DOUBLE(10,2) NOT NULL,
              res_ori_1 DOUBLE(14,8) NOT NULL,
              res_ori_2 DOUBLE(14,8) NOT NULL,
              res_ori_3 DOUBLE(14,8) NOT NULL,
              res_ori_4 DOUBLE(14,8) NOT NULL,
              res_ori_5 DOUBLE(14,8) NOT NULL,
              res_ori_6 DOUBLE(14,8) NOT NULL,
              res_ori_7 DOUBLE(14,8) NOT NULL,
              res_ori_8 DOUBLE(14,8) NOT NULL,
              res_ori_9 DOUBLE(14,8) NOT NULL,
              rotation100_rad DOUBLE(10,7),
              rotation010_rad DOUBLE(10,7),
              rotation001_rad DOUBLE(10,7),
              half_mosaicity_deg DOUBLE(10,7),
              wave_HE_ang DOUBLE(14,8),
              wave_LE_ang DOUBLE(14,8),
              domain_size_ang DOUBLE(10,2),
              unique_file_name MEDIUMTEXT
              )
            """
            ),
            (runtag+"_miller","""(
              hkl_id_1_base INTEGER PRIMARY KEY,
              h INTEGER NOT NULL,
              k INTEGER NOT NULL,
              l INTEGER NOT NULL
              )
            """
            ),
              ]
  def positional_refinement_schema_tables(self,runtag):
    return [(runtag+"_spotfinder","""
            (
              frame_id INTEGER, itile INTEGER,
              beam1x DOUBLE(10,2) NOT NULL,
              beam1y DOUBLE(10,2) NOT NULL,
              beamrx DOUBLE(10,2) NOT NULL,
              beamry DOUBLE(10,2) NOT NULL,
              spotfx DOUBLE(10,2) NOT NULL,
              spotfy DOUBLE(10,2) NOT NULL,
              spotcx DOUBLE(10,2) NOT NULL,
              spotcy DOUBLE(10,2) NOT NULL,
              h INTEGER NOT NULL,
              k INTEGER NOT NULL,
              l INTEGER NOT NULL,
              radialpx DOUBLE(6,3) NOT NULL DEFAULT 0.0,
              azimutpx DOUBLE(6,3) NOT NULL DEFAULT 0.0
            )
            """),
              ]
