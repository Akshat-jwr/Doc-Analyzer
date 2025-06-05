import { formatDistanceToNow, parseISO, format, addSeconds } from 'date-fns';

// Always adds 5.5 hours (19800 seconds) to UTC input to convert to IST
const toIST = (date: Date) => addSeconds(date, 19800);

// Takes a UTC date string or Date, returns "x minutes ago" in IST
export const formatTimeAgo = (dateInput: string | Date): string => {
  try {
    const utcDate = typeof dateInput === 'string' ? parseISO(dateInput) : dateInput;
    const istDate = toIST(utcDate);
    return formatDistanceToNow(istDate, { addSuffix: true });
  } catch (error) {
    console.error('Error in formatTimeAgo:', error);
    return 'Unknown time';
  }
};

// Takes a UTC date string or Date, returns formatted IST date and time
export const formatDateTime = (dateInput: string | Date): string => {
  try {
    const utcDate = typeof dateInput === 'string' ? parseISO(dateInput) : dateInput;
    const istDate = toIST(utcDate);
    return format(istDate, 'MMM dd, yyyy • hh:mm a');
  } catch (error) {
    console.error('Error in formatDateTime:', error);
    return 'Unknown date';
  }
};

// Takes a UTC date string or Date, returns formatted IST date
export const formatDateOnly = (dateInput: string | Date): string => {
  try {
    const utcDate = typeof dateInput === 'string' ? parseISO(dateInput) : dateInput;
    const istDate = toIST(utcDate);
    return format(istDate, 'MMM dd, yyyy');
  } catch (error) {
    console.error('Error in formatDateOnly:', error);
    return 'Unknown date';
  }
};

// Gets current time in IST
export const getCurrentTimeInIST = (): Date => {
  return toIST(new Date());
};

// Converts an IST date to UTC by subtracting 5.5 hours
export const localISTtoUTC = (istDate: Date): Date => {
  return addSeconds(istDate, -19800);
};
