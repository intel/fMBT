function mycounter(initial_value)
{
    this.value = initial_value

    this.inc = function () {
        this.value += 1
    }

    this.reset = function () {
        // Reset to zero in a not-that-funny way
        this.value = (this.value / this.value) - 1
    }

    this.count = function () {
        return this.value
    }
}
