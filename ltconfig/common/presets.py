#
# presets.py
#
# Copyright (C) 2017 Ratanak Lun <ratanakvlun@gmail.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Linking this software with other modules is making a combined work
# based on this software. Thus, the terms and conditions of the GNU
# General Public License cover the whole combination.
#
# As a special exception, the copyright holders of this software give
# you permission to link this software with independent modules to
# produce a combined work, regardless of the license terms of these
# independent modules, and to copy and distribute the resulting work
# under terms of your choice, provided that you also meet, for each
# linked module in the combined work, the terms and conditions of the
# license of that module. An independent module is a module which is
# not derived from or based on this software. If you modify this
# software, you may extend this exception to your version of the
# software, but you are not obligated to do so. If you do not wish to
# do so, delete this exception statement from your version.
#

MIN_MEMORY_USAGE = {
  "aio_threads": 1,
  "alert_queue_size": 100,
  "allow_multiple_connections_per_ip": False,
  "cache_buffer_chunk_size": 1,
  "cache_size": 0,
  "checking_mem_usage": 2,
  "close_redundant_connections": True,
  "coalesce_reads": False,
  "coalesce_writes": False,
  "connection_speed": 5,
  "contiguous_recv_buffer": False,
  "disk_io_read_mode": 2,
  "disk_io_write_mode": 2,
  "file_checks_delay_per_block": 5,
  "file_pool_size": 4,
  "inactivity_timeout": 120,
  "max_allowed_in_request_queue": 100,
  "max_failcount": 2,
  "max_http_recv_buffer_size": 1024 * 1024,
  "max_out_request_queue": 300,
  "max_paused_peerlist_size": 50,
  "max_peerlist_size": 500,
  "max_queued_disk_bytes": 1,
  "max_rejects": 10,
  "network_threads": 0,
  "optimize_hashing_for_speed": False,
  "prefer_udp_trackers": True,
  "prioritize_partial_pieces": True,
  "recv_socket_buffer_size": 16 * 1024,
  "send_buffer_watermark": 9,
  "send_socket_buffer_size": 16 * 1024,
  "upnp_ignore_nonrouters": True,
  "use_disk_read_ahead": False,
  "use_parole_mode": False,
  "use_read_cache": False,
  "utp_dynamic_sock_buf": False,
  "whole_pieces_threshold": 2
}

HIGH_PERFORMANCE_SEED = {
  "active_dht_limit": 600,
  "active_limit": 2000,
  "active_seeds": 2000,
  "active_tracker_limit": 2000,
  "aio_threads": 8,
  "alert_queue_size": 10000,
  "allow_multiple_connections_per_ip": True,
  "allowed_fast_set_size": 0,
  "auto_upload_slots": False,
  "cache_buffer_chunk_size": 0,
  "cache_expiry": 30,
  "cache_size": 32768 * 2,
  "checking_mem_usage": 320,
  "choking_algorithm": 0,
  "close_redundant_connections": True,
  "coalesce_reads": False,
  "coalesce_writes": False,
  "connection_speed": 500,
  "connections_limit": 8000,
  "dht_upload_rate_limit": 20000,
  "disk_cache_algorithm": 2,
  "explicit_read_cache": False,
  "file_pool_size": 500,
  "inactivity_timeout": 20,
  "listen_queue_size": 3000,
  "lock_disk_cache": False,
  "low_prio_disk": False,
  "max_allowed_in_request_queue": 2000,
  "max_failcount": 1,
  "max_http_recv_buffer_size": 6 * 1024 * 1024,
  "max_out_request_queue": 1500,
  "max_queued_disk_bytes": 7 * 1024 * 1024,
  "max_rejects": 10,
  "mixed_mode_algorithm": 0,
  "network_threads": 0,
  "no_atime_storage": True,
  "optimize_hashing_for_speed": True,
  "peer_timeout": 20,
  "read_cache_line_size": 32,
  "read_job_every": 100,
  "recv_socket_buffer_size": 1024 * 1024,
  "request_timeout": 10,
  "send_buffer_low_watermark": 1 * 1024 * 1024,
  "send_buffer_watermark": 3 * 1024 * 1024,
  "send_buffer_watermark_factor": 150,
  "send_socket_buffer_size": 1024 * 1024,
  "suggest_mode": 1,
  "unchoke_slots_limit": 2000,
  "use_disk_cache_pool": True,
  "use_read_cache": True,
  "utp_dynamic_sock_buf": True,
  "write_cache_line_size": 256
}
