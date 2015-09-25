/**
 * Copyright 2015 isandlaTech
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.cohorte.herald.utils;

import java.lang.Thread.State;
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;

import org.osgi.service.log.LogService;

/**
 * Implementation of Python's threading.Event
 *
 * @author Ahmad Shahwan
 */
public class Timer extends Event {

	/** State flag */
	private final AtomicBoolean pFlag;

	private LogService pLog = null;

	private final Set<Thread> pThreads;

	/**
	 * Sets up the event
	 */
	public Timer() {

		pFlag = new AtomicBoolean(false);
		pThreads = new HashSet<>();
	}

	/**
	 * Resets the internal flag to false
	 */
	@Override
	public void clear() {
		pFlag.set(false);
	}

	private void debug(final String msg) {
		if (pLog != null) {
			pLog.log(LogService.LOG_DEBUG, "== Timer == " + msg);
		}
	}

	/**
	 * Checks if the flag has been set
	 *
	 * @return True if the flag is set
	 */
	@Override
	public boolean isSet() {
		return pFlag.get();
	}

	/**
	 * Sets the internal flag to true.
	 */
	@Override
	public void set() {
		pFlag.set(true);

		Set<Thread> threads;
		synchronized (pThreads) {
			threads = new HashSet<>(pThreads);
		}

		for (Thread thread : threads) {
			if (thread.getState() == State.TIMED_WAITING) {
				thread.interrupt();
			}
		}
	}

	public void setLog(final LogService log) {
		pLog = log;
	}

	/**
	 * Blocks until the internal flag is true
	 *
	 * @return The state of the flag (true)
	 */
	@Override
	public boolean waitEvent() {
		while (!pFlag.get()) {
		}
		return true;
	}

	/**
	 * Blocks until the internal flag is true, or the time out is reached
	 *
	 * @param aTimeout
	 *            Maximum time to wait for the event (in milliseconds)
	 * @return The state of the flag
	 */
	@Override
	public boolean waitEvent(final Long aTimeout) {
		if (!pFlag.get()) {
			Thread current = Thread.currentThread();
			synchronized (pThreads) {
				if (pFlag.get()) {
					return true;
				}

				pThreads.add(current);
			}
			try {
				debug("Time to sleep: " + aTimeout);
				long start = System.currentTimeMillis();
				long target = start + aTimeout;
				while (System.currentTimeMillis() < target) {
					Thread.sleep(100);
					if (pFlag.get()) {
						break;
					}
				}
				long slept = System.currentTimeMillis() - start;
				debug("Time slept: " + slept);
				debug("Time overslept: " + (slept - aTimeout));
			} catch (InterruptedException ex) {
				// chill down
			} finally {
				synchronized (pThreads) {
					pThreads.remove(current);
				}
			}

		}
		return pFlag.get();
	}
}
