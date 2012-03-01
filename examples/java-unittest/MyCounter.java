import java.util.Random;

class MyCounter {
    public static boolean faulty = false;

    private Random r = new Random();

    public MyCounter() {
	if (!faulty) {
	    value = 0;
	} else {
	    value = r.nextInt();
	}
    }

    public void inc() {
	value++;
    }

    public void reset() {
	value = 0;
    }

    public int count() {
	return value;
    }

    private int value;
};
